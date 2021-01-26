#!/usr/bin/env python
"""
Send an email to all suppliers on a framework who have signed their framework
agreement. This can be used to, for example, let all suppliers know their
services are live.

Before using this script you should check that it has all the template
variables you need for your Notify template, and run it using `--dry-run` to
make sure it emails all the users you expect (and only them).

Uses the Notify API to send the email. This script *should not* resend emails.

Usage:
    scripts/framework-applications/notify-suppliers-with-signed-framework-agreement.py [options]
         [--supplier-id=<id> ... | --supplier-ids-from=<file>]
         <stage> <framework> <notify_api_key> <notify_template_id>

Example:
    scripts/framework-applications/notify-suppliers-with-signed-framework-agreement.py \
        preview g-cloud-11 $NOTIFY_API_KEY '98a9754d-9310-436a-9e7a-cc7504ecd92d'

Parameters:
    <stage>                     Environment to run script against.
    <framework>                 Slug of framework to run script against.
    <notify_api_key>            API key for GOV.UK Notify.
    <notify_template_id>        Template to send.

Options:
    --supplier-id=<id>          ID(s) of supplier(s) to email.
    --supplier-ids-from=<file>  Path to file containing supplier ID(s), one per line.

    -n, --dry-run               Run script without sending emails.

    -h, --help                  Show this screen.
"""
import sys
from typing import List
from docopt import docopt

sys.path.insert(0, ".")

from dmapiclient import DataAPIClient
from dmscripts.helpers.email_helpers import scripts_notify_client
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.supplier_data_helpers import get_supplier_ids_from_args, send_email_to_all_users_of_suppliers
from dmutils.env_helpers import get_api_endpoint_from_stage


logger = logging_helpers.configure_logger()


def get_supplier_ids_signed(api_client: DataAPIClient, framework_slug: str) -> List[int]:
    """
    Get a list of supplier IDs who are on `framework_slug` and have signed the framework agreement
    """
    return [
        supplier["supplierId"]
        for supplier in api_client.find_framework_suppliers_iter(
            framework_slug, agreement_returned=True, with_declarations=False
        )
        if supplier["onFramework"]
    ]


def get_email_addresses_for_supplier(api_client: DataAPIClient, supplier_id: int) -> List[str]:
    """Get the email addresses for each user belonging to `supplier_id`"""
    supplier_users = api_client.find_users_iter(supplier_id=supplier_id, personal_data_removed=False)
    return [user["emailAddress"] for user in supplier_users if user["active"]]


def get_previous_framework(framework: dict) -> dict:
    """Find the framework iteration that comes before `framework`

    Raises ValueError if the previous framework does not exist or cannot be
    found.
    """
    # TODO: Not convinced this is the best way to do this. Ideally we would use
    # the following framework information, but that is in the frameworks repo
    # and requires the content loader and some kind of reverse lookup that I
    # don't have time to reason out. Instead we assume that the framework
    # iteration immediately chronologically preceding the current iteration is
    # the correct one. Currently this holds true (in production at least).
    framework_family = framework["family"]
    frameworks_in_family = [fw for fw in api_client.find_frameworks()["frameworks"] if fw["family"] == framework_family]
    if not frameworks_in_family:
        raise ValueError(f"could not find any frameworks for family '{framework_family}'")
    if len(frameworks_in_family) < 2:
        raise ValueError(f"framework '{framework['slug']}' does not have a previous framework")

    frameworks_in_family.sort(key=lambda fw: fw["frameworkLiveAtUTC"])
    previous_framework = frameworks_in_family[-2]

    assert previous_framework["slug"] != framework["slug"]
    logger.info(f"found previous framework '{previous_framework['slug']}' for '{framework['slug']}'")

    return previous_framework


if __name__ == "__main__":
    arguments = docopt(__doc__)

    STAGE = arguments["<stage>"]
    FRAMEWORK_SLUG = arguments["<framework>"]
    NOTIFY_API_KEY = arguments["<notify_api_key>"]
    NOTIFY_TEMPLATE_ID = arguments["<notify_template_id>"]
    DRY_RUN = arguments["--dry-run"]

    mail_client = scripts_notify_client(NOTIFY_API_KEY, logger=logger)
    api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(STAGE),
        auth_token=get_auth_token("api", STAGE),
    )

    framework = api_client.get_framework(FRAMEWORK_SLUG).get("frameworks")
    previous_framework = get_previous_framework(framework)

    supplier_ids = get_supplier_ids_from_args(arguments)
    if supplier_ids is None:
        supplier_ids = get_supplier_ids_signed(api_client, FRAMEWORK_SLUG)

    send_email_to_all_users_of_suppliers(
        api_client,
        mail_client,
        supplier_ids,
        NOTIFY_TEMPLATE_ID,
        logger,
        personalisation={
            "framework_name": framework["name"],
            "previous_framework_name": previous_framework["name"],
        },
        is_dry_run=DRY_RUN
    )
