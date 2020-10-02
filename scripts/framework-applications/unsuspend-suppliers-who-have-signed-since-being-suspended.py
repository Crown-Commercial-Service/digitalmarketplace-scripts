#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
After a framework goes live, suppliers have a short period (usually 2 weeks) within which they must return their
signed framework agreement. If they have not returned their agreement, it cannot be countersigned by CCS and the
supplier will be unable to sell their services. We therefore temporarily suspend the supplier's services
so that buyers won't see them in search results (G-Cloud) or the supplier cannot apply to an opportunity (DOS).
If they later do sign their framework agreement we can then un-suspend them.

This script carries out the same action that a CCS Category user could perform in the admin, but in bulk.
In the past CCS have been responsible for unsuspending suppliers, however this script can be used to find and
unsuspend all suppliers who were suspended if we wish to do so for whatever reason.

Usage:
    scripts/framework-applications/unsuspend-suppliers-who-have-signed-since-being-suspended.py
        [-v...] [options]
        <stage> <framework> <output_dir>
        [--supplier-id=<id>... | --supplier-ids-from=<file>]
    scripts/framework-applications/unsuspend-suppliers-who-have-signed-since-being-suspended.py (-h | --help)

Options:
    <stage>                     Environment to run script against.
    <framework>                 Slug of framework to generate agreements for.
    <output_dir>                Output folder for list of email addresses to send notifications to.

    --supplier-id=<id>          ID of supplier to unsuspend.
    --supplier-ids-from=<file>  Path to file containing supplier IDs, one per line.

    --suspended-user=<user>     When searching for suppliers to unsuspend this argument specifies the user (or script)
                                who previously suspended the suppliers [default: Suspend services script].
    --suspended-date=<date>     The date when suppliers where previously unsuspended.

    -h, --help                  Show this help message

    -n, --dry-run               Run script without making changes.
    -v, --verbose               Show debug log messages.

    If neither `--supplier-ids-from` or `--supplier-id` are provided then
    all suppliers who without framework agreements will be suspended.
"""
import csv
import sys
import pathlib

from docopt import docopt

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.logging_helpers import (
    configure_logger,
    logging,
)
from dmscripts.helpers.framework_helpers import find_suppliers_without_agreements
from dmscripts.helpers.supplier_data_helpers import get_supplier_ids_from_args

from dmapiclient import DataAPIClient
from dmapiclient.audit import AuditTypes
from dmutils.env_helpers import get_api_endpoint_from_stage
from dmscripts.suspend_suppliers_without_agreements import (
    unsuspend_supplier_services, get_all_email_addresses_for_supplier
)


if __name__ == "__main__":
    args = docopt(__doc__)

    stage = args["<stage>"]
    framework_slug = args["<framework>"]

    dry_run = args["--dry-run"]
    verbose = args["--verbose"]
    output_dir = pathlib.Path(args["<output_dir>"])
    FILENAME = f'{framework_slug}-unsuspended-suppliers.csv'

    logger = configure_logger({
        "dmapiclient.base": logging.WARNING,
        "framework_helpers": logging.DEBUG if verbose >= 2 else logging.WARNING,
        "script": logging.DEBUG if verbose else logging.INFO,
    })

    client = DataAPIClient(
        get_api_endpoint_from_stage(args["<stage>"]),
        get_auth_token("api", args["<stage>"]),
    )

    framework = client.get_framework(framework_slug)["frameworks"]
    # Check that the framework is in live or standstill
    if framework['status'] not in ['live', 'standstill']:
        logger.error(f"Cannot suspend services for '{framework_slug}' with status {framework['status']}")
        exit(1)

    supplier_ids = get_supplier_ids_from_args(args)
    if not supplier_ids:
        # search for supplier who were suspended by --suspended-user
        find_audit_events = {
            "audit_date": args.get("--suspended-date"),
            "audit_type": AuditTypes.update_service_status,
            "user": args["--suspended-user"],
        }

        logger.debug(
            "searching for audit events with find_audit_events("
            "audit_date={audit_date!r}, audit_type={audit_type}, user={user!r})".format(**find_audit_events)
        )

        supplier_ids = set(event["data"]["supplierId"] for event in client.find_audit_events_iter(**find_audit_events))

    logger.info(f"going to try and un-suspend {len(supplier_ids)} suppliers")

    with open(output_dir / FILENAME, 'w') as csvfile:
        csv_headers = ['Supplier email', 'Supplier ID', "No. of services unsuspended"]

        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(csv_headers)

        for supplier_id in supplier_ids:
            framework_info = client.get_supplier_framework_info(supplier_id, framework_slug)

            if framework_info["frameworkInterest"]["agreementId"] is None:
                logger.warn(f"supplier {supplier_id} does not have a framework agreement, will not un-suspend")
                continue

            # Do the un-suspending
            unsuspended_service_count = unsuspend_supplier_services(
                client, logger, framework_slug, supplier_id, framework_info, dry_run
            )

            if unsuspended_service_count == 0:
                # We should have logged why already
                continue

            # Compile a list of email addresses for the supplier (to be sent via Notify) and add to the CSV
            for supplier_email in get_all_email_addresses_for_supplier(client, framework_info):
                writer.writerow([supplier_email, supplier_id, unsuspended_service_count])
