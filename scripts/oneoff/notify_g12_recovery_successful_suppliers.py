#!/usr/bin/env python
"""
Send an email to all suppliers who submitted services as part of G12 recovery

Before using this script you should check that it has all the template
variables you need for your Notify template, and run it using `--dry-run` to
make sure it emails all the users you expect (and only them).

Uses the Notify API to send the email. This script *should not* resend emails.

Usage:
    scripts/oneoff/notify_g12_recovery_successful_suppliers.py
        <path_to_recovery_csv> <notify_api_key> <notify_template_id> [--dry-run]

Parameters:
    <path_to_recovery_csv>      Path to CSV of recovery suppliers from https://govuk.zendesk.com/agent/tickets/4479646
    <notify_api_key>            API key for GOV.UK Notify.
    <notify_template_id>        Template to send.

Options:
    -n, --dry-run               Run script without sending emails.

    -h, --help                  Show this screen.
"""

import csv
import sys
from docopt import docopt
from itertools import chain

sys.path.insert(0, ".")

from dmapiclient import DataAPIClient
from dmscripts.helpers.supplier_data_helpers import get_email_addresses_for_supplier
from dmscripts.helpers.email_helpers import scripts_notify_client
from dmscripts.helpers import logging_helpers
from dmutils.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.email.helpers import hash_string

if __name__ == "__main__":
    logger = logging_helpers.configure_logger()
    arguments = docopt(__doc__)

    PATH_TO_RECOVERY_CSV = arguments["<path_to_recovery_csv>"]
    NOTIFY_API_KEY = arguments["<notify_api_key>"]
    NOTIFY_TEMPLATE_ID = arguments["<notify_template_id>"]
    DRY_RUN = arguments["--dry-run"]

    mail_client = scripts_notify_client(NOTIFY_API_KEY, logger=logger)
    api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage('production'),
        auth_token=get_auth_token("api", 'production'),
    )

    # Do the thing
    with open(PATH_TO_RECOVERY_CSV) as csvfile:
        supplier_ids = set([s['supplier_id'] for s in csv.DictReader(csvfile)
                            if s['draft_service_status'] == 'submitted'])

    # Flatten list of lists
    email_addresses = list(
        chain.from_iterable(get_email_addresses_for_supplier(api_client, supplier_id) for supplier_id in supplier_ids)
    )

    prefix = "[Dry Run] " if DRY_RUN else ""
    user_count = len(email_addresses)

    logger.info(f"Sending emails to {len(supplier_ids)} suppliers...")

    for count, email in enumerate(email_addresses, start=1):
        logger.info(f"{prefix}Sending email to supplier user {count} of {user_count}: {hash_string(email)}")
        if not DRY_RUN:
            mail_client.send_email(
                to_email_address=email,
                template_name_or_id=NOTIFY_TEMPLATE_ID,
                personalisation={
                    "framework_name": 'G-Cloud-12',
                },
            )
