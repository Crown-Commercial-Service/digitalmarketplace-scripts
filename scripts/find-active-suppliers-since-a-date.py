#!/usr/bin/env python3
"""
This script was needed to find all active registered suppliers, since a given date.

The script parses a date, provided by the user (if not default date of today is provided).
This date is then compared against the Suppliers list, where active is true.
If the date is more recent than the date the user provided, the record is captured and outputted.
A count is taken and also provided.

Usage:
    scripts/find-active-suppliers-since-a-date.py <stage> [options]

Options:
    --date=YYYY-MM-DD       Limit the number of suppliers to find [default: <today's date>]
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

if __name__ == "__main__":
    arguments = docopt(__doc__)
    stage = arguments['<stage>']
    user_date = arguments['--date']

    data_api_client = DataAPIClient(
        get_api_endpoint_from_stage(stage), get_auth_token("api", stage), user=get_user()
    )

    counter = 0
    date_format = "%Y-%m-%d"
    formatted_date = datetime.strptime(user_date, date_format) or datetime.now().strftime(date_format)

    with open(os.path.join(
        'data',
        'suppliers_registered_%s.csv' % datetime.now().strftime("%H:%M:%S")
    ), 'w', newline='') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(["email_address", "name", "supplierName", "supplierID"])

        for user in data_api_client.find_users_iter(role='supplier'):
            if user['active'] and datetime.strptime(
                user['createdAt'].split('T', 1)[0], date_format
            ) >= formatted_date:
                writer.writerow([
                    user['emailAddress'],
                    user['name'],
                    user['supplier']['name'],
                    user['supplier']['supplierId']
                ])
                counter += 1
            print(f"Total Records Count:{counter}", end="\r")
    print(f"Total Records Count:{counter}")
