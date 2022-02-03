#!/usr/bin/env python3
"""
For performance testing, we need suppliers who are able to copy services from the previous iteration of the framework.
Get up to 1000 suitable suppliers and then remove their data for the new framework so they're in a clean state for use
in tests.

Usage:
    scripts/get-suppliers-with-copyable-services.py <stage> <new-framework> <copy-from-framework> <output_dir> [options]

Options:
    --limit=LIMIT       Limit the number of suppliers to find [default: 1000]
"""
import sys

from dmapiclient import DataAPIClient, HTTPError
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
    OUTPUT_DIR = arguments['<output_dir>']
    SUPPLIER_LIMIT = int(arguments['--limit'])

    if stage == "production":
        raise Exception("This script is not safe to run in production")

    data_api_client = DataAPIClient(
        get_api_endpoint_from_stage(stage), get_auth_token("api", stage), user=get_user()
    )
    new_framework_slug = arguments['<new-framework>']
    copy_from_framework_slug = arguments['<copy-from-framework>']

    suppliers_on_old_framework = data_api_client.find_framework_suppliers_iter(
        copy_from_framework_slug,
        agreement_returned=True
    )

    print("Building CSV with supplier accounts")

    if not os.path.exists(OUTPUT_DIR):
        print("Creating {} directory".format(OUTPUT_DIR))
        os.makedirs(OUTPUT_DIR)

    with open(os.path.join(OUTPUT_DIR, f"supplier-accounts-{new_framework_slug}.csv"), "w", newline='') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(["supplier_id", "email_address", "password"])

        count = 0

        for supplier in suppliers_on_old_framework:
            if count >= SUPPLIER_LIMIT:
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

            print(f"Suppliers found: {count}/{SUPPLIER_LIMIT}", end='\r')
            writer.writerow([supplier_id, user['emailAddress'], DEFAULT_PASSWORD])

        print(f"Suppliers found: {count}/{SUPPLIER_LIMIT}")
