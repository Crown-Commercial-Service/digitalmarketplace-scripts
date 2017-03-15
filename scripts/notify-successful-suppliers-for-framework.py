#!/usr/bin/env python
"""Email suppliers who have at least one successful lot entry on the given framework.
Uses the Notify API to inform suppliers of success result.

Usage:
    scripts/notify-successful-suppliers-for-framework.py <stage> <api_token> <framework_slug>
        <govuk_notify_api_key> <govuk_notify_template_id>

Example:
    scripts/notify-successful-suppliers-for-framework.py preview myToken g-cloud-8
        my-awesome-key govuk_notify_template_id

Options:
    -h, --help  Show this screen
"""
import sys

sys.path.insert(0, '.')
from docopt import docopt

from dmapiclient import DataAPIClient
from dmutils.email.dm_notify import DMNotifyClient
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging
from dmscripts.helpers.supplier_data_helpers import SuccessfulSupplierContextForNotify

logger = logging_helpers.configure_logger({"dmapiclient": logging.INFO})


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    API_TOKEN = arguments['<api_token>']
    FRAMEWORK_SLUG = arguments['<framework_slug>']
    GOVUK_NOTIFY_API_KEY = arguments['<govuk_notify_api_key>']
    GOVUK_NOTIFY_TEMPLATE_ID = arguments['<govuk_notify_template_id>']

    mail_client = DMNotifyClient(GOVUK_NOTIFY_API_KEY, logger=logger)
    api_client = DataAPIClient(base_url=get_api_endpoint_from_stage(STAGE), auth_token=API_TOKEN)

    context_helper = SuccessfulSupplierContextForNotify(api_client, FRAMEWORK_SLUG)
    context_helper.populate_data()
    context_data = context_helper.get_users_peronalisations()

    for user_email, personalisation in context_data.items():
        logger.info(user_email)
        mail_client.send_email(user_email, GOVUK_NOTIFY_TEMPLATE_ID, personalisation, allow_resend=False)
