#!/usr/bin/env python
"""
This script attempts to swap the DUNS numbers for two suppliers. This involves temporarily setting one of the suppliers
to a fake DUNS number to satisfy the database's uniqueness constraint.

Usage: swap-supplier-duns.py <supplier_1> <supplier_2> <duns_1> <duns_2> [options]

    <supplier_1>                                          Supplier ID #1
    <supplier_2>                                          Supplier ID #2
    <duns_1>                                              DUNS number #1
    <duns_2>                                              DUNS number #2

Options:
    --stage=<stage>                                       Stage to target
    --updated-by=<updated-by>                             Updater email address for audit trail
    --dummy-duns=<dummy-duns>                             Dummy DUNS number
    --dry-run                                             List actions that would have been taken
    -h, --help                                            Show this screen

"""
import sys
from dmapiclient.data import DataAPIClient

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt


UPDATER = "duns_number swap script"
DUMMY_DUNS = '0000000002'


def swap_duns(supplier_id_1, supplier_id_2, new_duns_1, new_duns_2):
    if dry_run:
        return f"Would swap suppliers {supplier_id_1} and {supplier_id_2} swapped to {new_duns_1} and {new_duns_2}"

    # Supplier 2 set to dummy
    data_api_client.update_supplier(supplier_id_2, {"dunsNumber": dummy_duns}, UPDATER)

    # Supplier 1 set to new 1
    data_api_client.update_supplier(supplier_id_1, {"dunsNumber": new_duns_1}, UPDATER)

    # Supplier 2 set to new 2
    data_api_client.update_supplier(supplier_id_2, {"dunsNumber": new_duns_2}, UPDATER)

    return f"Suppliers {supplier_id_1} and {supplier_id_2} swapped to {new_duns_1} and {new_duns_2} successfully"


def check_types(supplier1, supplier2, duns1, duns2):
    if not len(duns1) == 9:
        print(f"DUNS {duns1} must be 9 digits")
        return False
    if not len(duns2) == 9:
        print(f"DUNS {duns2} must be 9 digits")
        return False
    try:
        int(supplier1)
    except ValueError:
        print(f"Supplier ID {supplier1} is not an int")
        return False
    try:
        int(supplier2)
    except ValueError:
        print(f"Supplier ID {supplier2} is not an int")
        return False
    return True


def check_existing_duns(supplier1, supplier2, duns1, duns2):
    # Check if supplier1 already has new duns 1
    existing_supplier1 = data_api_client.get_supplier(supplier1)
    if existing_supplier1['suppliers']['dunsNumber'] == duns1:
        print(f"Supplier {supplier1} already has DUNS {duns1}")
        return False

    # Check if supplier2 already has new duns 2
    existing_supplier2 = data_api_client.get_supplier(supplier2)
    if existing_supplier2['suppliers']['dunsNumber'] == duns2:
        print(f"Supplier {supplier2} already has DUNS {duns2}")
        return False

    # Check that supplier1 has new duns 2 to swap from
    if existing_supplier1['suppliers']['dunsNumber'] != duns2:
        print(f"Supplier {supplier1} does not have DUNS {duns2}")
        return False

    # Check that supplier2 has new duns 1 to swap from
    if existing_supplier2['suppliers']['dunsNumber'] != duns1:
        print(f"Supplier {supplier2} does not have DUNS {duns1}")
        return False

    # Check that the duns numbers are different
    if duns1 == duns2:
        print(f"DUNS numbers are identical: {duns1}")
        return False

    return True


def dummy_duns_in_use(dummy_duns):
    result = data_api_client.find_suppliers(duns_number=dummy_duns)
    return result['meta']['total']


if __name__ == "__main__":
    arguments = docopt(__doc__)

    # Get script arguments
    stage = arguments['--stage'] or 'local'
    supplier1 = arguments['<supplier_1>']
    supplier2 = arguments['<supplier_2>']
    duns1 = arguments['<duns_1>']
    duns2 = arguments['<duns_2>']

    updated_by = arguments['--updated-by'] or UPDATER
    dummy_duns = arguments['--dummy-duns']
    dry_run = arguments['--dry-run'] or None

    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token('api', stage)
    )

    if dummy_duns:
        # Check if user-supplied dummy DUNS is in use
        if dummy_duns_in_use(dummy_duns):
            print(f"Dummy DUNS {dummy_duns} is already in use. Please use another number.")
            exit(1)
    else:
        # Check if the default dummy DUNS is in use
        if dummy_duns_in_use(DUMMY_DUNS):
            print(f"Default dummy DUNS {DUMMY_DUNS} is already in use. Please supply another with --dummy-duns.")
            exit(1)
        dummy_duns = DUMMY_DUNS

    if check_types(supplier1, supplier2, duns1, duns2):
        if check_existing_duns(supplier1, supplier2, duns1, duns2):
            result = swap_duns(supplier1, supplier2, duns1, duns2)
            print(result)
