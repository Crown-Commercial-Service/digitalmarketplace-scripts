#!/usr/bin/env python3
"""
For testing, we need suppliers who have only applied up to a certain framework agreement.
These logins will be output to a CSV file in the data (or specified) directory.

Usage:
    scripts/get-suppliers-on-last-specified-framework.py <stage> <framework_slug> [options]

Options:
    --output-dir=<output_dir>       Location to store CSV file [default: data]
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
G_CLOUD_FRAMEWORKS = [
    'g-cloud-4',
    'g-cloud-5',
    'g-cloud-6',
    'g-cloud-7',
    'g-cloud-8',
    'g-cloud-9',
    'g-cloud-10',
    'g-cloud-11',
    'g-cloud-12'
]
DOS_FRAMEWORKS = [
    'digital-outcomes-and-specialists',
    'digital-outcomes-and-specialists-2',
    'digital-outcomes-and-specialists-3',
    'digital-outcomes-and-specialists-4',
    'digital-outcomes-and-specialists-5'
]


def get_unwanted_frameworks(framework_slug):
    if framework_slug[0] == 'g':
        framework_list = G_CLOUD_FRAMEWORKS
    else:
        framework_list = DOS_FRAMEWORKS

    unwnated_frameworks_start_index = framework_list.index(framework_slug) + 1

    return framework_list[unwnated_frameworks_start_index:]


if __name__ == "__main__":
    arguments = docopt(__doc__)
    stage = arguments['<stage>']
    framework_slug = arguments['<framework_slug>']
    output_dir = arguments['--output-dir']

    if stage == "production":
        raise Exception("This script is not safe to run in production")

    if framework_slug not in G_CLOUD_FRAMEWORKS and framework_slug not in DOS_FRAMEWORKS:
        raise Exception("You entered an unrecognised framework")

    unwanted_framework_slugs = get_unwanted_frameworks(framework_slug)

    data_api_client = DataAPIClient(
        get_api_endpoint_from_stage(stage), get_auth_token("api", stage), user=get_user()
    )

    suppliers_frameworks = data_api_client.find_framework_suppliers_iter(framework_slug)

    unwanted_supplier_ids = []

    for slug in unwanted_framework_slugs:
        unwanted_supplier_ids += [
            framework['supplierId'] for framework in data_api_client.find_framework_suppliers_iter(slug)
        ]

    if not os.path.exists(output_dir):
        print("Creating {} directory".format(output_dir))
        os.makedirs(output_dir)

    with open(os.path.join(
        output_dir,
        f"supplier-accounts-applied-up-to-{framework_slug}.csv"),
        "w",
        newline=''
    ) as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(["supplier_id", "email_address", "password"])

        for suppliers_framework in suppliers_frameworks:

            supplier_id = suppliers_framework['supplierId']

            if supplier_id in unwanted_supplier_ids:
                continue

            try:
                user = next(u for u in data_api_client.find_users_iter(supplier_id=supplier_id) if u['active'])
            except StopIteration:
                continue

            writer.writerow([supplier_id, user['emailAddress'], DEFAULT_PASSWORD])
