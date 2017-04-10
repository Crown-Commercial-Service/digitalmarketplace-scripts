#!/usr/bin/env python

"""
Description:
    For every lot the script will:
        - look for latest briefs for Digital Outcomes and Specialists
        - if there are new briefs on that lot:
            - it will create a Mailchimp campaign
            - it will set the content of the campaign to be the briefs found
            - it will send that campaign to the list_id as referenced in the `lots` variable
        - if there are no new briefs on that lot no campaign is created or sent

    Number of days tells the script for how many days before current date it should include in its search for briefs
        example:  if you run this script on a Wednesday and set number of days=1,
                    then it will only include briefs from Tuesday (preceding day).
        example2: if you run it on Wednesday and set number of days=3,
                    then it will include all briefs published on Sunday, Monday and Tuesday.

Usage:
    send_dos_opportunities_email.py <stage> <api_token> <mailchimp_username> <mailchimp_api_key> <number_of_days>

Example:
    send_dos_opportunities_email.py preview b7g5r7e6gv876tv6 user@gds.gov.uk 7483crh87h34c3£@£ 3
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
