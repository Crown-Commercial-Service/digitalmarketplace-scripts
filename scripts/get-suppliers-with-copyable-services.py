#!/usr/bin/env python3
"""
For performance testing, we need suppliers who are able to copy services from the previous iteration of the framework.
Get up to 1000 suitable suppliers and then remove their data for the new framework so they're in a clean state for use
in tests.

Usage:
    scripts/get-suppliers-with-copyable-services.py <stage> <new-framework> <copy-from-framework> [options]

Options:
    --limit=<limit>             Limit the number of suppliers to find (default is 1000)
    --output-dir=<output_dir>   Directory to write to CSV file, if not given it will print to the console
"""
import sys

from dmapiclient import DataAPIClient, HTTPError
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt
import os

sys.path.insert(0, ".")

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.updated_by_helpers import get_user

try:
    import unicodecsv as csv
except ImportError:
    import csv

# We don't want to use _all_ the suppliers. There should be ~5000 eligible suppliers.
SUPPLIER_LIMIT = 1000

DEFAULT_PASSWORD = "Password1234"


if __name__ == "__main__":
    arguments = docopt(__doc__)
    stage = arguments['<stage>']
    OUTPUT_DIR = arguments['--output-dir']

    if stage == "production":
        raise Exception("This script is not safe to run in production")
    if not OUTPUT_DIR:
        raise Exception("You must specify an output directory for the file")

    if arguments['--limit']:
        supplier_limit = int(arguments['--limit'])
    else:
        supplier_limit = SUPPLIER_LIMIT

    data_api_client = DataAPIClient(
        get_api_endpoint_from_stage(stage), get_auth_token("api", stage), user=get_user()
    )
    new_framework_slug = arguments['<new-framework>']
    copy_from_framework_slug = arguments['<copy-from-framework>']

    suppliers_on_old_framework = data_api_client.find_framework_suppliers_iter(
        copy_from_framework_slug,
        agreement_returned=True
    )

    print(f"Building CSV with supplier accounts")

    if not os.path.exists(OUTPUT_DIR):
        print("Creating {} directory".format(OUTPUT_DIR))
        os.makedirs(OUTPUT_DIR)

    with open(os.path.join(OUTPUT_DIR, f"supplier-accounts-{new_framework_slug}.csv"), "wb") as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(["supplier_id", "email_address", "password"])

        count = 0

        for supplier in suppliers_on_old_framework:
            if count >= supplier_limit:
                break

            supplier_id = supplier['supplierId']
            for service in data_api_client.find_draft_services_iter(supplier_id, framework=new_framework_slug):
                data_api_client.delete_draft_service(service['id'])

            try:
                data_api_client.remove_supplier_declaration(92197, new_framework_slug)
                data_api_client.set_supplier_framework_application_company_details_confirmed(
                    supplier_id, new_framework_slug, False
                )
            except HTTPError as e:
                if not (e.status_code == 404 and "has not registered interest" in e.message):
                    raise

            try:
                user = next(u for u in data_api_client.find_users_iter(supplier_id=supplier_id) if u['active'])
            except StopIteration:
                continue

            count += 1

            print(f"Suppliers found: {count}/{supplier_limit}", end='\r')
            writer.writerow([supplier_id, user['emailAddress'], "Password1234"])

        print(f"Suppliers found: {supplier_limit}/{supplier_limit}")
