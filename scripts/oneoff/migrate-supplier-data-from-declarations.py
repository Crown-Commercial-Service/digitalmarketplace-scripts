#!/usr/bin/env python
"""Selectively migrate supplier information from a recent framework declaration to new fields on supplier itself

Usage:
    scripts/oneoff/migrate-supplier-data-from-declarations.py <stage> <data_api_token> <ch_api_token> <framework_slugs>
        [<user>] [--dry-run]

Positional arguments:
    <stage>                                 API stage to perform operation on
    <data_api_token>                        appropriate API token for <stage>
    <ch_api_token>                          API token for companies house API
    <framework_slugs>                       comma-separated whitelist of framework slugs to inspect for source data
                                            (in order specified)

Optional arguments:
    -h, --help                              show this help message and exit
    --dry-run                               skip upload of modifications
"""
import sys
sys.path.insert(0, '.')

import re
from pprint import pformat
import logging
import getpass

import backoff
from docopt import docopt
import requests
from dateutil.parser import parse as dateutil_parse
from dmapiclient import DataAPIClient, HTTPError
from dmapiclient.errors import HTTPTemporaryError

from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers.logging_helpers import configure_logger
from dmscripts.helpers.logging_helpers import INFO as loglevel_INFO


logger = logging.getLogger("script")


_backoff_wrap = backoff.on_exception(
    backoff.expo,
    (HTTPTemporaryError, requests.exceptions.ConnectionError),
    max_tries=5,
)


@_backoff_wrap
def _chid_exists(chid, chapi_token):
    response = requests.get(
        "https://api.companieshouse.gov.uk/company/{}".format(chid),
        auth=(chapi_token, ""),
    )
    if response.status_code == 404:
        logger.info("chid %s does not seem to exist", repr(chid))
        return False
    elif response.status_code == 200:
        logger.info("chid %s seems to exist", repr(chid))
        return True
    else:
        raise RuntimeError("Requesting CHAPI page for chid %s resulted in a %s response" % (chid, response.status_code))


_only_digits_alpha_re = re.compile("[^0-9A-Z]")
_chid_validation_re = re.compile("^([0-9]{2}|[A-Z]{2})[0-9]{6}$")


def _normalize_chid(in_data):
    if not in_data:
        return None
    stripped = _only_digits_alpha_re.sub("", in_data.upper())
    padded = ("O" + stripped) if stripped[0] == "C" and len(stripped) == 7 else stripped.rjust(8, "0")
    return padded if _chid_validation_re.match(padded) else None


def _catch_404_none(func):
    try:
        return func()
    except HTTPError as e:
        if e.status_code == 404:
            return None
        else:
            raise


if __name__ == '__main__':
    arguments = docopt(__doc__)

    configure_logger({"script": loglevel_INFO})

    client = DataAPIClient(get_api_endpoint_from_stage(arguments['<stage>']), arguments['<data_api_token>'])
    user = arguments['<user>'] or getpass.getuser()
    framework_slugs = arguments.get("<framework_slugs>") and arguments["<framework_slugs>"].split(",")
    dry_run = bool(arguments.get("--dry-run"))

    frameworks = tuple(client.get_framework(framework_slug)["frameworks"] for framework_slug in framework_slugs)

    logger.info("Inspecting framework declarations in this order: %s", ", ".join(fw["slug"] for fw in frameworks))

    for supplier in client.find_suppliers_iter():
        logger.info("Processing supplier %s", supplier["id"])
        try:
            supplier_framework = next(
                sfr["frameworkInterest"] for sfr in (
                    _catch_404_none(
                        _backoff_wrap(
                            lambda: client.get_supplier_framework_info(supplier["id"], framework["slug"])
                        )
                    ) for framework in frameworks
                ) if sfr and sfr["frameworkInterest"]["onFramework"]
            )
        except StopIteration:
            logger.info("Supplier %s: not on any relevant frameworks", supplier["id"])
            supplier_framework = None
        else:
            logger.info(
                "Supplier %s: using data from framework %s",
                supplier["id"],
                supplier_framework["frameworkSlug"],
            )

        supplier_update = {}
        if supplier_framework:
            supplier_update.update({
                "registeredName": supplier_framework["declaration"]["nameOfOrganisation"],
                "vatNumber": supplier_framework["declaration"]["registeredVATNumber"],
                "tradingStatus": (
                    supplier_framework["declaration"]["tradingStatus"]
                    if supplier_framework["declaration"]["tradingStatus"] != "other (please specify)" else
                    supplier_framework["declaration"]["tradingStatusOther"]
                ),
            })

            if "dunsNumber" in supplier_framework["declaration"]:
                supplier_update["dunsNumber"] = supplier_framework["declaration"]["dunsNumber"]

            try:
                supplier_update["registrationDate"] = dateutil_parse(
                    supplier_framework["declaration"]["firstRegistered"],
                    dayfirst=True,
                    fuzzy=True,
                ).date().isoformat()
            except ValueError:
                logger.info(
                    "Supplier %s: unable to parse date from %s",
                    supplier["id"],
                    repr(supplier_framework["declaration"]["firstRegistered"]),
                )

        supplier_update["registrationCountry"] = (
            # ISO 3166-1 alpha-2 code
            "gb" if supplier_framework and supplier_framework["declaration"].get("establishedInTheUK") else ""
        )

        try:
            supplier_update["companiesHouseNumber"] = next(
                normalized_chid for normalized_chid in (
                    _normalize_chid(chid_candidate) for chid_candidate in (
                        supplier_framework and supplier_framework["declaration"]["companyRegistrationNumber"],
                        supplier.get("companiesHouseNumber"),
                    )
                ) if normalized_chid and _chid_exists(normalized_chid, arguments['<ch_api_token>'])
            )
        except StopIteration:
            logger.info("Supplier %s: no appropriate chid found", supplier["id"])
            supplier_update["companiesHouseNumber"] = None

        contact = supplier["contactInformation"][0]
        contact_update = {}
        if supplier_framework and "registeredAddressBuilding" in supplier_framework["declaration"]:
            contact_update.update({
                "address1": supplier_framework["declaration"]["registeredAddressBuilding"],
                "city": supplier_framework["declaration"]["registeredAddressTown"],
                "postcode": supplier_framework["declaration"]["registeredAddressPostcode"],
            })
        elif (contact.get("address2") or "").strip():
            # rescue any remaining data in address2
            contact_update["address1"] = u", ".join((contact["address1"].strip(), contact["address2"].strip()))

        # we're going to deprecate this field
        contact_update["address2"] = ""

        # the following _backoff_wrap-wrapped calls are a little ugly as `backoff` is designed as a function decorator
        # and we really want to retry inline blocks, so we're declaring them as lambdas which we immediately execute
        # after decoration
        logger.info("supplier_update = %s", pformat(supplier_update))
        if not dry_run:
            _backoff_wrap(lambda: client.update_supplier(supplier["id"], supplier_update, user=user))()

        logger.info("contact_update = %s", pformat(contact_update))
        if not dry_run:
            _backoff_wrap(lambda: client.update_contact_information(
                supplier["id"],
                contact["id"],
                contact_update,
                user=user,
            ))()
