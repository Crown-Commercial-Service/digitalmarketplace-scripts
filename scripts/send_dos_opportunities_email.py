#!/usr/bin/env python

"""Description to be added here

Usage:
    send_dos_opportunities_email.py <stage> <api_token> <mailchimp_username> <mailchimp_api_key> <number_of_days>
"""

import sys

from docopt import docopt
from mailchimp3 import MailChimp
from dmapiclient import DataAPIClient

sys.path.insert(0, '.')
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.send_dos_opportunities_email import main


lots = [
    {
        "lot_slug": "digital-specialists",
        "lot_name": "Digital specialists",
        "list_id": "096e52cebb"
    },
    {
        "lot_slug": "digital-outcomes",
        "lot_name": "Digital outcomes",
        "list_id": "096e52cebb"
    },
    {
        "lot_slug": "user-research-participants",
        "lot_name": "User research participants",
        "list_id": "096e52cebb"
    }
]


if __name__ == "__main__":
    arguments = docopt(__doc__)

    api_url = get_api_endpoint_from_stage(arguments['<stage>'])
    data_api_client = DataAPIClient(api_url, arguments['<api_token>'])

    mailchimp_client = MailChimp(arguments['<mailchimp_username>'], arguments['<mailchimp_api_key>'])

    for lot_data in lots:
        ok = main(
            data_api_client=data_api_client,
            mailchimp_client=mailchimp_client,
            lot_data=lot_data,
            number_of_days=int(arguments['<number_of_days>'])
        )

    if not ok:
        sys.exit(1)
