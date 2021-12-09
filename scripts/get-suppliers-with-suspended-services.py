#!/usr/bin/env python3
"""
For testing, we need suppliers who have suspended services.
Gets up to 20 suitable suppliers who have a disabled service in the relvent framework.
This will be output to CSV file in the data directory (by default).

Usage:
    scripts/get-suppliers-with-suspended-services.py <stage> <framework_slug> [options]

Options:
    --limit=<limit>               Limit the number of suppliers to find [default: 20]
    --output-dir=<output_dir>     Specify where the CSV should be out put to [default: data]
"""
import sys

from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt
import os
import csv

sys.path.insert(0, ".")

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.updated_by_helpers import get_user


DEFAULT_PASSWORD = "Password1234"

if __name__ == "__main__":
    arguments = docopt(__doc__)
    stage = arguments['<stage>']
    framework_slug = arguments['<framework_slug>']
    limit = int(arguments['--limit'])
    output_dir = arguments['--output-dir']

    if stage == "production":
        raise Exception("This script is not safe to run in production")

    data_api_client = DataAPIClient(
        get_api_endpoint_from_stage(stage), get_auth_token("api", stage), user=get_user()
    )

    suspended_services = data_api_client.find_services_iter(framework=framework_slug, status="disabled")

    if not os.path.exists(output_dir):
        print("Creating {} directory".format(output_dir))
        os.makedirs(output_dir)

    with open(os.path.join(
        output_dir,
        f"supplier-accounts-with-suspended-services-{framework_slug}.csv"),
        "w",
        newline=''
    ) as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(["service_name", "service_id", "supplier_id", "email_address", "password"])

        count = 0

        for suspended_service in suspended_services:
            if count >= limit:
                break

            supplier_id = suspended_service['supplierId']

            try:
                user = next(u for u in data_api_client.find_users_iter(supplier_id=supplier_id) if u['active'])
            except StopIteration:
                continue

            count += 1

            print(f"Suppliers found: {count}/{limit}", end='\r')
            writer.writerow([
                suspended_service['serviceName'],
                suspended_service['id'],
                supplier_id,
                user['emailAddress'],
                DEFAULT_PASSWORD
            ])

    print(f"Suppliers found: {count}/{limit}")
