#!/usr/bin/env python3
"""
For performance testing, we need suppliers who have completed their application but have not signed the
framework agreement.
Get up to 500 suitable suppliers who meet these requirements based on the information in the declaration schema.
This will be output to CSV file in the specified directory.

Usage:
    scripts/get-suppliers-with-unsigned-framework-agreements.py <stage> <framework_slug> <output_dir> [options]

Options:
    --limit=LIMIT       Limit the number of suppliers to find [default: 500]
"""
import sys

from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt
from collections import Counter
import os
import csv

sys.path.insert(0, ".")

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.updated_by_helpers import get_user


DEFAULT_PASSWORD = "Password1234"


def _assess_draft_services(framework_slug, supplier_id,):
    # A supplier must have at least 1 submitted service
    counter = Counter()

    for draft_service in data_api_client.find_draft_services_by_framework_iter(framework_slug, supplier_id=supplier_id):
        counter[draft_service["status"]] += 1

    return counter


if __name__ == "__main__":
    arguments = docopt(__doc__)
    stage = arguments['<stage>']
    framework_slug = arguments['<framework_slug>']
    OUTPUT_DIR = arguments['<output_dir>']
    SUPPLIER_LIMIT = int(arguments['--limit'])

    if stage == "production":
        raise Exception("This script is not safe to run in production")

    data_api_client = DataAPIClient(
        get_api_endpoint_from_stage(stage), get_auth_token("api", stage), user=get_user()
    )

    suppliers_frameworks = data_api_client.find_framework_suppliers_iter(framework_slug)

    print(f"Building CSV with supplier accounts")

    if not os.path.exists(OUTPUT_DIR):
        print("Creating {} directory".format(OUTPUT_DIR))
        os.makedirs(OUTPUT_DIR)

    with open(os.path.join(OUTPUT_DIR, f"supplier-accounts-{framework_slug}.csv"), "w", newline='') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(["supplier_id", "email_address", "password"])

        count = 0

        for supplier_framework in suppliers_frameworks:
            supplier_id = supplier_framework['supplierId']

            # Skip suppliers who have already passed?
            if supplier_framework["onFramework"] is True:
                continue

            # Skip suppliers who have not completed their decleration?
            if supplier_framework["declaration"].get("status") != "complete":
                continue

            # A supplier should have at least one valid service to pass their application
            service_counter = _assess_draft_services(framework_slug, supplier_id)

            if not service_counter["submitted"]:
                continue

            # If all the above are satisfied then the supplier should be acceptable to use for performance testing

            try:
                user = next(u for u in data_api_client.find_users_iter(supplier_id=supplier_id) if u['active'])
            except StopIteration:
                continue

            count += 1

            print(f"Suppliers found: {count}/{SUPPLIER_LIMIT}", end='\r')
            writer.writerow([supplier_id, user['emailAddress'], DEFAULT_PASSWORD])

        print(f"Suppliers found: {count}/{SUPPLIER_LIMIT}")
