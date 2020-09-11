#!/usr/bin/env python
"""
Email suppliers who have at least one successful lot entry on the given framework.
This is also known as the 'Intention To Award' email, where we instruct successful suppliers to sign
their framework agreement.

Uses the Notify API to inform suppliers of success result. This script *should not* resend emails.

Usage:
    scripts/framework-applications/notify-successful-suppliers-for-framework.py [options]
         [--supplier-id=<id> ... | --supplier-ids-from=<file>]
         <stage> <framework> <notify_api_key> <notify_template_id>

Example:
    scripts/framework-applications/notify-successful-suppliers-for-framework.py preview g-cloud-11 api-key template-id

Options:
    <stage>                     Environment to run script against.
    <framework>                 Slug of framework to run script against.
    <notify_api_key>            API key for GOV.UK Notify.

    --supplier-id=<id>          ID(s) of supplier(s) to email.
    --supplier-ids-from=<file>  Path to file containing supplier ID(s), one per line.

    -n, --dry-run               Run script without sending emails.

    -h, --help                  Show this screen.
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
    SuccessfulSupplierContextForNotify,
    get_supplier_ids_from_args,
)
from dmutils.env_helpers import get_api_endpoint_from_stage

logger = logging_helpers.configure_logger({"dmapiclient": logging.INFO})


if __name__ == '__main__':
    arguments = docopt(__doc__)
    supplier_ids = get_supplier_ids_from_args(arguments)

    STAGE = arguments['<stage>']
    FRAMEWORK_SLUG = arguments['<framework>']
    GOVUK_NOTIFY_API_KEY = arguments['<notify_api_key>']
    GOVUK_NOTIFY_TEMPLATE_ID = arguments['<notify_template_id>']
    DRY_RUN = arguments['--dry-run']

    mail_client = scripts_notify_client(GOVUK_NOTIFY_API_KEY, logger=logger)
    api_client = DataAPIClient(base_url=get_api_endpoint_from_stage(STAGE), auth_token=get_auth_token('api', STAGE))

    context_helper = SuccessfulSupplierContextForNotify(
        api_client, FRAMEWORK_SLUG, supplier_ids=supplier_ids, logger=logger
    )
    context_helper.populate_data()
    context_data = context_helper.get_users_personalisations()

    prefix = "[Dry Run] " if DRY_RUN else ""

    # TODO: fetch and format these dates from the API if possible
    # Add in any framework-specific dates etc here
    extra_template_context = {
        "intentionToAwardAt_dateformat": "12 September 2020",
        "frameworkLiveAt_dateformat": "28 September 2020",
    }

    for user_email, personalisation in context_data.items():
        logger.info(f"{prefix}Sending email to supplier user '{hash_string(user_email)}'")

        personalisation.update(extra_template_context)

        if DRY_RUN:
            continue

        try:
            mail_client.send_email(user_email, GOVUK_NOTIFY_TEMPLATE_ID, personalisation, allow_resend=False)
        except EmailError as e:
            logger.error(f"Error sending email to supplier user '{hash_string(user_email)}': {e}")
