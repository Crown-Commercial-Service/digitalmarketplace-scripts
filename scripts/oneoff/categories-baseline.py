#!/usr/bin/env python
"""Usage: categories-baseline.py <g-cloud-version> [--output-folder=OUTPUT] [--stage=STAGE]

This very basic script is run for our performance analyst. It gives them an idea of what categories services are being
offered under. It also shows who is a reseller, and who is selling original products. As this script hammers the API to
get DUNS numbers, I strongly recommend it's only run locally against a recent database dump. So I've written the script
to default to 'local' and users will need to specifically ask it to run against a different stage.

The script generates three files, one for each lot. By default it drops them into the local folder,
ie digitalmarketplace-scripts/
If you'd like them to go somewhere else, supply a folder path to --output-path

The script doesn't output any logging, but if you run it with DMRunner you can watch as it zooms through the API. It
takes about 15m to run through G-Cloud 10, which has about 25,000 items.

Options:
    <g-cloud-version>                                     Which iteration of G-Cloud to target. Use g-cloud-x format

    [--stage=STAGE]                                       Stage to target

    [--output-folder=OUTPUT]                              Folder in which the reports should go

    -h, --help                                            Show this screen

"""
import sys
import os
from dmapiclient.data import DataAPIClient

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt

if __name__ == "__main__":
    arguments = docopt(__doc__)

    # Get script arguments
    stage = arguments['--stage'] or 'local'
    version = arguments['<g-cloud-version>']
    OUTPUT_DIR = arguments['--output-folder'] or '.'

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Set defaults, instantiate clients
    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token('api', stage)
    )

    hosting_services = data_api_client.find_services_iter(
        framework=f'{version}', status='published', lot='cloud-hosting'
    )
    software_services = data_api_client.find_services_iter(
        framework=f'{version}', status='published', lot='cloud-software'
    )
    support_services = data_api_client.find_services_iter(
        framework=f'{version}', status='published', lot='cloud-support'
    )

    lots = {
        'hosting': hosting_services,
        'software': software_services,
        'support': support_services
    }
    headers = [
        'Supplier ID', 'DUNS Number', 'Supplier Name', 'Reseller?', 'Service Name', 'Organisation Size', 'Categories'
    ]
    for lot, services_in_lot in lots.items():
        with open(os.path.join(OUTPUT_DIR, f'{lot}-categories-{version}.tsv'), 'w') as f:
            f.write('\t'.join(headers))
            for service in services_in_lot:
                supplier_data = data_api_client.get_supplier(service.get('supplierId'))['suppliers']
                row = [
                    str(service['supplierId']),
                    supplier_data.get('dunsNumber'),
                    service.get('supplierName'),
                    'false' if service.get('resellingType') == 'not_reseller' else 'true',
                    service.get('serviceName'),
                    service.get('id'),
                    supplier_data.get('organisationSize'),
                    '\t'.join(service.get('serviceCategories')) if service.get('serviceCategories') else ''
                ]
                f.write('\t'.join(row) + '\n')
