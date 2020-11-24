#!/usr/bin/env python3

"""Get active users as a CSV

Outputs a CSV suitable for sending one-off service updates via Notify.

Usage: scripts/get_active_users_csv.py <stage>

Example
    scripts/get_active_users_csv.py preview > output.csv
"""

import csv
import sys

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt
from dmapiclient import DataAPIClient


if __name__ == '__main__':
    arguments = docopt(__doc__)

    stage = arguments['<stage>']
    data_api_client = DataAPIClient(get_api_endpoint_from_stage(stage), get_auth_token('api', stage))

    writer = csv.writer(sys.stdout)
    writer.writerow(['email address'])
    for user in filter(lambda u: u['active'], data_api_client.find_users_iter(personal_data_removed=False)):
        writer.writerow([user['emailAddress']])
