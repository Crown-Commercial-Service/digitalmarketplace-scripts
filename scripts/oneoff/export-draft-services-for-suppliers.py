#!/usr/bin/env python
"""Usage: export-draft-services-for-suppliers.py <framework_slug> <stage> [<supplier_id_file>] [--output-folder=OUTPUT]

Given a list of supplier IDs, output all draft services as a CSV to the given --output-folder, with columns as follows:
 - supplierId
 - supplierName
 - serviceName
 - draftId
 - status
 - lotName
 - validationErrors

"""
import sys
import csv
import os
from dmapiclient.data import DataAPIClient

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers.supplier_data_helpers import get_supplier_ids_from_file
from docopt import docopt


if __name__ == "__main__":
    arguments = docopt(__doc__)

    # Get script arguments
    stage = arguments['<stage>'] or 'local'
    OUTPUT_DIR = arguments['--output-folder'] or '.'

    # Get supplier IDs from file
    supplier_id_file = arguments['<supplier_id_file>']
    supplier_ids = get_supplier_ids_from_file(supplier_id_file)

    framework_slug = arguments['<framework_slug>']

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Initialise Data API client
    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token('api', stage)
    )

    headers = [
        'Supplier ID', 'Supplier Name', 'Service Name', 'Draft ID', 'Status', 'Lot Name', 'Validation Errors',
    ]

    with open(os.path.join(OUTPUT_DIR, f'{framework_slug}-draft-services.csv'), 'w', newline='') as f:
        writer = csv.writer(f, delimiter=',', quotechar='"')
        writer.writerow(headers)

        for supplier_id in supplier_ids:
            print("Supplier ID", supplier_id)
            drafts = data_api_client.find_draft_services_by_framework_iter(
                framework_slug, supplier_id=supplier_id
            )
            for d in drafts:
                validation_errors = data_api_client.get_draft_service(d['id']).get('validationErrors')
                row = [
                    str(d['supplierId']),
                    d.get('supplierName'),
                    d.get('serviceName'),
                    d['id'],
                    d['status'],
                    d['lotName'],
                    ",".join(list(validation_errors.keys()))
                ]
                writer.writerow(row)
