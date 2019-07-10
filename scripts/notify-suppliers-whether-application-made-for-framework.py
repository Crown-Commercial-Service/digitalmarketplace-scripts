#!/usr/bin/env python3
"""
Email all suppliers who registered interest in applying to a framework about whether or not they made an application.

Uses the Notify API to send emails. This script *should not* resend emails.

Usage:
    scripts/notify-suppliers-whether-application-made-for-framework.py [options]
         [--supplier-id=<id> ... | --supplier-ids-from=<file>]
         <stage> <framework> <notify_api_key>

Example:
    scripts/notify-suppliers-whether-application-made-for-framework.py --dry-run preview g-cloud-9 my-awesome-key

Options:
    <stage>                     Environment to run script against.
    <framework>                 Framework slug.
    <notify_api_key>            API key for GOV.UK Notify.

    --supplier-id=<id>          ID(s) of supplier(s) to email.
    --supplier-ids-from=<file>  Path to file containing supplier ID(s), one per line.

    -n, --dry-run               Run script without sending emails.

    -h, --help                  Show this screen
"""
import sys

sys.path.insert(0, '.')
from docopt import docopt

from dmapiclient import DataAPIClient
from dmutils.email.exceptions import EmailError
from dmutils.email.helpers import hash_string
from dmscripts.helpers.email_helpers import scripts_notify_client
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging
from dmscripts.helpers.supplier_data_helpers import (
    AppliedToFrameworkSupplierContextForNotify,
    get_supplier_ids_from_args,
)
from dmutils.env_helpers import get_api_endpoint_from_stage

logger = logging_helpers.configure_logger({"dmapiclient": logging.INFO})

NOTIFY_TEMPLATES = {
    'application_made': 'de02a7e3-80f6-4391-818c-48326e1f4688',
    'application_not_made': '87a126b4-7909-4b63-b981-d3c3d6a558ff'
}


if __name__ == '__main__':
    arguments = docopt(__doc__)
    supplier_ids = get_supplier_ids_from_args(arguments)

    STAGE = arguments['<stage>']
    FRAMEWORK_SLUG = arguments['<framework>']
    GOVUK_NOTIFY_API_KEY = arguments['<notify_api_key>']
    DRY_RUN = arguments['--dry-run']

    mail_client = scripts_notify_client(GOVUK_NOTIFY_API_KEY, logger=logger)
    api_client = DataAPIClient(base_url=get_api_endpoint_from_stage(STAGE),
                               auth_token=get_auth_token('api', STAGE))

    context_helper = AppliedToFrameworkSupplierContextForNotify(api_client, FRAMEWORK_SLUG, supplier_ids=supplier_ids)
    context_helper.populate_data()
    prefix = "[Dry Run] " if DRY_RUN else ""
    error_count = 0
    for supplier_id, users in context_helper.get_suppliers_with_users_personalisations():
        logger.info(f"{prefix}Supplier '{supplier_id}'")

        for user, personalisation in users:
            user_email = user["email address"]
            template_key = 'application_made' if personalisation['applied'] else 'application_not_made'
            template = NOTIFY_TEMPLATES[template_key]

            logger.info(
                f"{prefix}Sending '{template_key}' email to supplier '{supplier_id}' user '{hash_string(user_email)}'")

            if DRY_RUN:
                continue

            try:
                mail_client.send_email(user_email, template, personalisation, allow_resend=False)
            except EmailError as e:
                logger.error(f"Error sending email to supplier '{supplier_id}' user '{hash_string(user_email)}': {e}")
                error_count += 1

    sys.exit(error_count)
