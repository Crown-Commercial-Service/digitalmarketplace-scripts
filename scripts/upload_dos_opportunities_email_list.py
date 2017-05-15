#!/usr/bin/env python

"""
Description:
    upload_dos_opportunities_email_list

Usage:
    upload_dos_opportunities_email_list.py <stage> <api_token>

Example:
    upload_dos_opportunities_email_list.py preview myToken

"""

import sys

from docopt import docopt
from dmapiclient import DataAPIClient

sys.path.insert(0, '.')
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.upload_dos_opportunities_email_list import main


lots = [
    {
        "lot_slug": "digital-specialists",
        "list_id": "07c21f0451",
        "framework_slug": "digital-outcomes-and-specialists-2"
    }
]


if __name__ == '__main__':
    arguments = docopt(__doc__)

    api_url = get_api_endpoint_from_stage(arguments['<stage>'])
    data_api_client = DataAPIClient(api_url, arguments['<api_token>'])

    for lot_data in lots:
        main(data_api_client, lot_data)
