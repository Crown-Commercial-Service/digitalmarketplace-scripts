#!/usr/bin/env python3

"""Export supplier responses to subcontracting questions

Outputs a CSV of supplier responses to DOS subcontracting questions to stdout
Usage:
    export_dos_supplier_subcontracting_responses.py <stage> <framework>

Example:
    export_dos_supplier_subcontracting_responses.py production digital-outcomes-and-specialists-5 > subcontracting.csv
"""

import csv
import sys

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt
from dmapiclient import DataAPIClient
from dmscripts.helpers.framework_helpers import find_suppliers_on_framework


if __name__ == '__main__':
    arguments = docopt(__doc__)
    stage = arguments['<stage>']
    framework = arguments['<framework>']

    data_api_client = DataAPIClient(get_api_endpoint_from_stage(stage), get_auth_token('api', stage))

    def get_subcontracting_dict(supplier_id, declaration_fields, supplier_fields):
        id = {'supplierId': supplier_id}
        declaration = (data_api_client.get_supplier_framework_info(supplier_id, framework)['frameworkInterest']
                       .get('declaration'))
        supplier = data_api_client.get_supplier(supplier_id)['suppliers']
        declaration_fields = {fieldname: declaration.get(fieldname) for fieldname in declaration_fields}
        supplier_fields = {fieldname: supplier.get(fieldname) for fieldname in supplier_fields}
        return {**id, **declaration_fields, **supplier_fields}

    declaration_fields = ['subcontracting', 'subcontracting30DayPayments', 'subcontractingInvoicesPaid']
    supplier_fields = ['name', 'organisationSize', 'dunsNumber', 'companiesHouseNumber']
    fieldnames = ['supplierId'] + declaration_fields + supplier_fields

    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    suppliers = find_suppliers_on_framework(data_api_client, framework)
    for supplier in suppliers:
        supplier_id = supplier['supplierId']
        writer.writerow(get_subcontracting_dict(supplier_id, declaration_fields, supplier_fields))
