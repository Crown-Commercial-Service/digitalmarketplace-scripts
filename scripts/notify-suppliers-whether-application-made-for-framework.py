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
from dmscripts.helpers.email_helpers import scripts_notify_client
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging
from dmscripts.helpers.supplier_data_helpers import get_supplier_ids_from_args

from dmutils.env_helpers import get_api_endpoint_from_stage
from dmscripts.notify_suppliers_whether_application_made_for_framework import notify_suppliers_whether_application_made

logger = logging_helpers.configure_logger({"dmapiclient": logging.INFO})


if __name__ == '__main__':
    arguments = docopt(__doc__)
    supplier_ids = get_supplier_ids_from_args(arguments)

    stage = arguments['<stage>']

    mail_client = scripts_notify_client(arguments['<notify_api_key>'], logger=logger)
    api_client = DataAPIClient(base_url=get_api_endpoint_from_stage(stage),
                               auth_token=get_auth_token('api', stage))

    error_count = notify_suppliers_whether_application_made(
        api_client,
        mail_client,
        arguments['<framework>'],
        logger=logger,
        dry_run=arguments['--dry-run'],
        supplier_ids=supplier_ids,
    )
    sys.exit(error_count)
