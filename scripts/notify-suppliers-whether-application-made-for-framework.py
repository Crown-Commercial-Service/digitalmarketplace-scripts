#!/usr/bin/env python
"""Email all suppliers who registered interest in applying to a framework about whether or not they made an application.
Uses the Notify API to send emails.

Usage:
    scripts/notify-suppliers-whether-application-made-for-framework.py <stage> <api_token> <framework_slug>
        <govuk_notify_api_key> [--dry-run]

Example:
    scripts/notify-suppliers-whether-application-made-for-framework.py preview myToken g-cloud-9
        my-awesome-key --dry-run

Options:
    -h, --help  Show this screen
"""
import sys

sys.path.insert(0, '.')  # noqa
from docopt import docopt

from dmapiclient import DataAPIClient
from dmutils.email.dm_notify import DMNotifyClient
from dmutils.email.exceptions import EmailError
from dmutils.dates import update_framework_with_formatted_dates
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging
from dmscripts.helpers.supplier_data_helpers import AppliedToFrameworkSupplierContextForNotify

logger = logging_helpers.configure_logger({"dmapiclient": logging.INFO})

NOTIFY_TEMPLATE_APPLICATION_MADE = 'de02a7e3-80f6-4391-818c-48326e1f4688'
NOTIFY_TEMPLATE_NO_APPLICATION = '87a126b4-7909-4b63-b981-d3c3d6a558ff'


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    API_TOKEN = arguments['<api_token>']
    FRAMEWORK_SLUG = arguments['<framework_slug>']
    GOVUK_NOTIFY_API_KEY = arguments['<govuk_notify_api_key>']
    DRY_RUN = arguments['--dry-run']

    mail_client = DMNotifyClient(GOVUK_NOTIFY_API_KEY, logger=logger)
    api_client = DataAPIClient(base_url=get_api_endpoint_from_stage(STAGE), auth_token=API_TOKEN)

    framework_data = api_client.get_framework(FRAMEWORK_SLUG)['frameworks']
    update_framework_with_formatted_dates(framework_data)

    context_helper = AppliedToFrameworkSupplierContextForNotify(api_client,
                                                                FRAMEWORK_SLUG,
                                                                framework_data['intentionToAwardAt'])
    context_helper.populate_data()
    context_data = context_helper.get_users_personalisations()
    error_count = 0
    for user_email, personalisation in context_data.items():
        logger.info(user_email)
        template_id = (NOTIFY_TEMPLATE_APPLICATION_MADE
                       if personalisation['applied']
                       else NOTIFY_TEMPLATE_NO_APPLICATION)
        if DRY_RUN:
            logger.info("[Dry Run] Sending email {} to {}".format(template_id, user_email))
        else:
            try:
                mail_client.send_email(user_email, template_id, personalisation, allow_resend=False)
            except EmailError as e:
                logger.error(u'Error sending email to {}: {}'.format(user_email, e))
                error_count += 1

    sys.exit(error_count)
