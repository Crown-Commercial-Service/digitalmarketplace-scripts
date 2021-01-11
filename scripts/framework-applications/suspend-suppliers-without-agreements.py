#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
After a framework goes live, suppliers have a short period (usually 2 weeks) within which they must return their
signed framework agreement. If they have not returned their agreement, it cannot be countersigned by CCS and the
supplier will be unable to sell their services. We should therefore temporarily suspend the supplier's services
so that buyers won't see them in search results (G-Cloud) or the supplier cannot apply to an opportunity (DOS).
Suppliers who have returned an incorrect agreement file ('on-hold') should not be suspended.

This script suspends suppliers who have not signed their agreement and sends them a reminder email.
In the past CCS has provided a list of supplier IDs that should be suspended, however this script can also
suspend all suppliers who have not returned a framework agreement.

Usage:
    scripts/framework-applications/suspend-suppliers-without-agreements.py
        [-v...] [options]
        <stage> <framework> <notify_api_key> <frameworks_path>
        [--supplier-id=<id>... | --supplier-ids-from=<file>]
    scripts/framework-applications/suspend-suppliers-without-agreements.py (-h | --help)

Options:
    <stage>                     Environment to run script against.
    <framework>                 Slug of framework to generate agreements for.
    <notify_api_key>            API key for GOV.UK Notify.
    <frameworks_path>           Path to digitalmarketplace-frameworks repository

    --supplier-id=<id>          ID of supplier to generate agreement page for.
    --supplier-ids-from=<file>  Path to file containing supplier IDs, one per line.

    -h, --help                  Show this help message

    -n, --dry-run               Run script without sending emails.
    -v, --verbose               Show debug log messages.

    If neither `--supplier-ids-from` or `--supplier-id` are provided then
    all suppliers without framework agreements will be suspended.
"""
import sys

from docopt import docopt
from dmcontent import ContentLoader
from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage
from dmutils.email.helpers import hash_string

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.logging_helpers import (
    configure_logger,
    logging,
)
from dmscripts.helpers.framework_helpers import find_suppliers_without_agreements
from dmscripts.helpers.supplier_data_helpers import get_supplier_ids_from_args
from dmscripts.helpers.email_helpers import scripts_notify_client
from dmscripts.suspend_suppliers_without_agreements import (
    suspend_supplier_services, get_all_email_addresses_for_supplier
)

NOTIFY_TEMPLATE_ID = "f4224b66-42cc-45c3-b55a-2cf5cb95792f"


def get_framework_contract_title(frameworks_path: str, framework_slug: str) -> str:
    """The contract title is different for G-Cloud and DOS. Look up the correct name with the content loader"""
    content_loader = ContentLoader(frameworks_path)
    content_loader.load_messages(framework_slug, ["e-signature"])
    return str(content_loader.get_message(framework_slug, "e-signature", "framework_contract_title"))


if __name__ == "__main__":
    args = docopt(__doc__)

    stage = args["<stage>"]
    framework_slug = args["<framework>"]

    dry_run = args["--dry-run"]
    verbose = args["--verbose"]
    NOTIFY_API_KEY = args["<notify_api_key>"]
    FRAMEWORKS_PATH = args["<frameworks_path>"]

    prefix = "[Dry run] " if dry_run else ""

    logger = configure_logger({
        "dmapiclient.base": logging.WARNING,
        "framework_helpers": logging.DEBUG if verbose >= 2 else logging.WARNING,
        "script": logging.DEBUG if verbose else logging.INFO,
    })

    client = DataAPIClient(
        get_api_endpoint_from_stage(args["<stage>"]),
        get_auth_token("api", args["<stage>"]),
    )

    notify_client = scripts_notify_client(NOTIFY_API_KEY, logger=logger)

    framework = client.get_framework(framework_slug)["frameworks"]
    # Check that the framework is in live or standstill
    if framework['status'] not in ['live', 'standstill']:
        logger.error(f"Cannot suspend services for '{framework_slug}' with status {framework['status']}")
        exit(1)

    supplier_ids = get_supplier_ids_from_args(args)
    suppliers = find_suppliers_without_agreements(client, framework_slug, supplier_ids)

    framework_name = framework["name"]
    contract_title = get_framework_contract_title(FRAMEWORKS_PATH, framework_slug)

    for supplier in suppliers:
        supplier_id = supplier["supplierId"]
        framework_info = client.get_supplier_framework_info(supplier_id, framework_slug)

        logger.info(f"{prefix}Suspending services for supplier {supplier_id}")
        if not dry_run:
            # Do the suspending
            suspended_service_count = suspend_supplier_services(
                client, logger, framework_slug, supplier_id, framework_info, dry_run
            )

            if suspended_service_count > 0:
                logger.info(f"{prefix}Suspended {suspended_service_count} services for supplier {supplier_id}")
            else:
                logger.warning(f"{prefix}Something went wrong - suspended 0 services for supplier {supplier_id}")

        # Send the reminder email to all users for that supplier
        for supplier_email in get_all_email_addresses_for_supplier(client, framework_info):
            logger.info(f"{prefix}Sending email to supplier user: {hash_string(supplier_email)}")
            if not dry_run:
                notify_client.send_email(
                    to_email_address=supplier_email,
                    template_name_or_id=NOTIFY_TEMPLATE_ID,
                    personalisation={
                        "framework_name": framework_name,
                        "framework_slug": framework_slug,
                        "contract_title": contract_title
                    }
                )
