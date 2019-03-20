#!/usr/bin/env python
"""Usage: update-supplier-data.py <path-to-updates> [--stage=STAGE] [--attribute=ATTRIBUTE] [--dry-run]

This script iterates through a CSV and updates a supplier with one of three values: DUNS number, company registration
number, or company name.

The DUNS number is an interesting problem, as there are cases where suppliers have used a number that belongs to another
supplier. When the rightful owner attempts to add it, they are told they can't as it's already in use. This is due to a
UNIQUE restriction on the database column. For now, those cases will simply be logged and you'll need to work out what
to do with them separately.

Options:
    <path-to-updates>                                     The path to the CSV containing updates

    [--stage=STAGE]                                       Stage to target

    [--attribute=ATTRIBUTE]                               Attribute to update

    [--dry-run]                                           List actions that would have been taken

    -h, --help                                            Show this screen

"""
import sys
import csv
import re
from dmapiclient.data import DataAPIClient

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt
from pathlib import Path
from dmapiclient.errors import HTTPError


UPDATER = "update supplier data script"


def update_supplier_attribute(row):
    attribute_map = {
        "DUNS Number": update_duns,
        "Company registration number": update_company_number,
        "Company registered name": update_company_name,
    }
    supplier_id = row.get("DMP record ID")
    new_value = row.get("New Value")
    field_to_change = row.get("Field Name for update")
    print(f'Updating {row.get("Field Name for update")} to {row.get("New Value")}')
    try:
        attribute_map.get(field_to_change)(supplier_id, new_value)
    except HTTPError as e:
        print(f"Error updating supplier {supplier_id} with error {e}")


def update_duns(supplier_id, new_duns):
    try:
        data_api_client.update_supplier(supplier_id, {"dunsNumber": new_duns}, UPDATER)
    except HTTPError:
        print(f'The DUNS number {new_duns} is already in use')


def update_company_number(supplier_id, new_number):
    companies_house_regex = re.compile('^([0-9]{2}|[A-Za-z]{2})[0-9]{6}$')
    if companies_house_regex.match(new_number):
        data_api_client.update_supplier(supplier_id, {"companiesHouseNumber": new_number}, UPDATER)
    else:
        data_api_client.update_supplier(supplier_id, {"otherCompanyRegistrationNumber": new_number}, UPDATER)


def update_company_name(supplier_id, new_name):
    data_api_client.update_supplier(supplier_id, {"registeredName": new_name}, UPDATER)


if __name__ == "__main__":
    arguments = docopt(__doc__)

    # Get script arguments
    stage = arguments['--stage'] or 'local'
    path_to_updates = arguments['<path-to-updates>']
    attribute = arguments['--attribute']
    dry_run = arguments['--dry-run']

    # Set defaults, instantiate clients
    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token('api', stage)
    )

    with open(Path(path_to_updates), 'r') as f:
        updates = csv.DictReader(f)
        non_existent_suppliers = []
        for row in updates:
            if not dry_run:
                update_supplier_attribute(row)
            else:
                supplier_id = int(row.get("DMP record ID"))
                try:
                    supplier_to_change = data_api_client.get_supplier(supplier_id)['suppliers']
                    name = supplier_to_change.get('registeredName')
                    print(f'Current name: {name}')
                except HTTPError as e:
                    print(f'{supplier_id} does not exist')
                    print(f'HTTPError: {e}')
                    non_existent_suppliers.append(supplier_id)
                print(
                    f'Would update supplier id: {row.get("DMP record ID")} with new {row.get("Field Name for update")},'
                    f'value {row.get("New Value")}'
                )
                print(f'There are {len(non_existent_suppliers)} non-existent suppliers')
        print(non_existent_suppliers)
