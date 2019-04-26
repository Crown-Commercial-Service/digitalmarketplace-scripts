#!/usr/bin/env python
"""Usage: export-service-categories.py <g-cloud-version> [--output-folder=OUTPUT] [--stage=STAGE]

Basic services export, for use by the DM performance analyst.
Outputs a .tsv file per lot to the given --output-folder, with columns as follows:
 - supplierId
 - dunsNumber
 - supplierName
 - reseller (true/false)
 - serviceName
 - serviceId
 - organisationSize
 - serviceCategories (tab separated list)

Defaults to 'local' - recommend running the export against a recent cleaned production dump to avoid hammering the
production API.
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


SUPPORT_CATEGORIES = {
    'QAAndTesting': 'Quality assurance and performance testing',
    'setupAndMigrationService': 'Setup and migration\tPlanning',
    'securityTesting': 'Security services',
    'ongoingSupport': 'Ongoing support',
    'training': 'Training'
}


def cloud_support_categories(service_data):
    # Cloud support categories are not stored in `serviceCategories` for ¯\_(ツ)_/¯ reasons
    # The Elasticsearch mapping hardcodes the categories based on certain field values
    categories = []
    for field, category_name in SUPPORT_CATEGORIES.items():
        if service_data.get(field):
            categories.append(category_name)
    return categories


def get_categories(lot_name, service_data):
    if lot_name == 'support':
        return '\t'.join(cloud_support_categories(service_data))
    return '\t'.join(service.get('serviceCategories')) if service.get('serviceCategories') else ''


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
        'Supplier ID', 'DUNS Number', 'Supplier Name', 'Reseller?', 'Service Name', 'Service Description', 'Organisation Size', 'Categories',
        '\n'
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
                    service.get('serviceDescription'),
                    'false' if service.get('resellingType') == 'not_reseller' else 'true',
                    service.get('serviceName'),
                    service.get('id'),
                    supplier_data.get('organisationSize'),
                    get_categories(lot, service)
                ]
                f.write('\t'.join(row) + '\n')
