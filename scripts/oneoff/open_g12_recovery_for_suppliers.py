#!/usr/bin/env python
"""
Inform suppliers involved in the G12 recovery that the process is now open for them.

Usage:
    scripts/oneoff/open_g12_recovery_for_suppliers.py <stage> <notify_api_key> [--dry-run]

Parameters:
    <stage>                     Environment to run script against.
    <notify_api_key>            API key for GOV.UK Notify.

Options:
    -n, --dry-run               Run script without sending emails.
    -h, --help                  Show this screen.

Before running this script, ensure that the list of suppliers in the credentials is correct.
"""

import sys

from dmapiclient import DataAPIClient
from dmutils.email.helpers import hash_string
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt

sys.path.insert(0, ".")

from dmscripts.helpers import logging_helpers
from dmscripts.helpers.auth_helpers import get_g12_suppliers, get_auth_token
from dmscripts.helpers.email_helpers import scripts_notify_client
from dmscripts.helpers.supplier_data_helpers import get_email_addresses_for_supplier

NOTIFY_TEMPLATE_ID = "347e1ed7-ec83-45a0-bb16-832f244f8919"

if __name__ == "__main__":
    arguments = docopt(__doc__)

    stage = arguments["<stage>"]
    dry_run = arguments["--dry-run"]
    notify_api_key = arguments["<notify_api_key>"]

    logger = logging_helpers.configure_logger()
    mail_client = scripts_notify_client(notify_api_key, logger=logger)
    api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token("api", stage),
    )

    user_emails = [
        supplier_user
        for supplier_id in get_g12_suppliers(stage)
        for supplier_user in get_email_addresses_for_supplier(api_client, supplier_id)
    ]

    print(user_emails)

    user_count = len(user_emails)
    prefix = "[Dry Run] " if dry_run else ""
    for count, email in enumerate(user_emails, start=1):
        logger.info(
            f"{prefix}Sending email to supplier user {count} of {user_count}: {hash_string(email)}"
        )
        if not dry_run:
            mail_client.send_email(
                to_email_address=email,
                template_name_or_id=NOTIFY_TEMPLATE_ID,
            )
