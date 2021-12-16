#!/usr/bin/env python3
"""
This will find all users, that are a Supplier and also active, that have been created since a given date.

The script parses a date, provided by the user, (if not default today's date is provided as a default).
This date is then taken and compared against the created dates of the returned looped list of suppliers,
where active is true.
If the creation date of the user is more recent than the compared date the user provided,
the record is captured and outputted. A count is also taken and outputted.

Usage:
    scripts/find-active-suppliers-since-a-date.py <stage> [options]

Options:
    --date=YYYY-MM-DD       Limit the number of suppliers to find [default: ]
"""
import sys
import os
import csv

from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt
from datetime import datetime

sys.path.insert(0, ".")

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.updated_by_helpers import get_user
from dmscripts.helpers.datetime_helpers import parse_datetime

if __name__ == "__main__":
    arguments = docopt(__doc__)
    stage = arguments['<stage>']

    data_api_client = DataAPIClient(
        get_api_endpoint_from_stage(stage), get_auth_token("api", stage), user=get_user()
    )

    date = arguments['--date'] or datetime.now().strftime("%Y-%m-%d")
    counter = 0

    if not os.path.exists('data'):
        os.makedirs('data')

    with open(os.path.join(
        'data',
        'suppliers_registered_%s.csv' % datetime.now().strftime("%H:%M:%S")
    ), 'w', newline='') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(["email_address", "name", "supplierName", "supplierID"])

        for user in data_api_client.find_users_iter(role='supplier'):
            if user['active'] and parse_datetime(user['createdAt'].split('T', 1)[0]) >= parse_datetime(date):
                writer.writerow([
                    user['emailAddress'],
                    user['name'],
                    user['supplier']['name'],
                    user['supplier']['supplierId']
                ])
                counter += 1
            print(f"Total Records Count:{counter}", end="\r")
    print(f"Total Records Count:{counter}")
