#!/usr/bin/env python3

"""
Description:
    For every lot the script will:
    - find a list of emails for all suppliers and their users from the API
    - add new emails to mailchimp list if they're not there. If the user previously unsubscribed themselves
    from the list, they will not be subscribed when the script runs.

    Please be aware that sometimes there can be a delay (up to a few minutes) in adding new addresses
    to a mailchimp user list after an API call has been made. Unfortunately we couldn't find mailchimp documentation
    regarding this.

    If in the command line you provide an environment other than production the script will run on test lists
    that we have setup on mailchimp.

Usage:
    upload-dos-opportunities-email-list.py <stage> <mailchimp_username> <mailchimp_api_key> <framework_slug>

Example:
    upload-dos-opportunities-email-list.py preview user@gds.gov.uk 7483crh87h34c3 digital-outcomes-and-specialists-3

"""

import sys

from docopt import docopt
from dmapiclient import DataAPIClient
from dmutils.email.dm_mailchimp import DMMailChimpClient

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.upload_dos_opportunities_email_list import main
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging
from dmutils.env_helpers import get_api_endpoint_from_stage

LOT_SLUGS = ('digital-specialists', 'digital-outcomes', 'user-research-participants')

logger = logging_helpers.configure_logger({'dmapiclient': logging.INFO})


if __name__ == '__main__':
    arguments = docopt(__doc__)
    framework_slug = arguments['<framework_slug>']
    stage = arguments['<stage>']

    list_ids = {
        'digital-outcomes-and-specialists-2': {
            'digital-specialists': "30ba9fdf39" if stage == "production" else "07c21f0451",
            'digital-outcomes': "97952fee38" if stage == "production" else "f0077c516d",
            'user-research-participants': "e6b93a3bce" if stage == "production" else "d35601203b",
        },
        'digital-outcomes-and-specialists-3': {
            'digital-specialists': "bee802d641" if stage == "production" else "07c21f0451",
            'digital-outcomes': "5c92c78a78" if stage == "production" else "f0077c516d",
            'user-research-participants': "34ebe0bffa" if stage == "production" else "d35601203b",
        },
        'digital-outcomes-and-specialists-4': {
            'digital-specialists': "29d06d5201" if stage == "production" else "07c21f0451",
            'digital-outcomes': "4360debc5a" if stage == "production" else "f0077c516d",
            'user-research-participants': "2538f8a0f1" if stage == "production" else "d35601203b",
        },
        'digital-outcomes-and-specialists-5': {
            'digital-specialists': "246fac2d9a" if stage == "production" else "07c21f0451",
            'digital-outcomes': "eebeddcc2b" if stage == "production" else "f0077c516d",
            'user-research-participants': "f497856d31" if stage == "production" else "d35601203b",
        },
    }

    lots = [
        {'lot_slug': lot_slug, 'list_id': list_ids[framework_slug][lot_slug], 'framework_slug': framework_slug}
        for lot_slug in LOT_SLUGS
    ]

    api_url = get_api_endpoint_from_stage(stage)
    data_api_client = DataAPIClient(api_url, get_auth_token('api', stage))
    dm_mailchimp_client = DMMailChimpClient(
        arguments['<mailchimp_username>'],
        arguments['<mailchimp_api_key>'],
        logger,
        retries=3
    )

    for lot_data in lots:
        main(data_api_client, dm_mailchimp_client, lot_data, logger)
