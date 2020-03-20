#!/usr/bin/env python
"""Usage: gcloud-service-attribute-export.py <framework-slug> [--output-folder=OUTPUT] [--stage=STAGE]

Export a subset of live service info.

Defaults to 'local' - recommend running the export against a recent cleaned production dump to avoid hammering the
production API.
The script doesn't output any logging, but if you run it with DMRunner you can watch as it zooms through the API. It
takes about 15m to run through G-Cloud 10, which has about 25,000 items.

Change the service attributes below depending on what you want to export. For example, to export
'serviceDefinitionDocumentURL', edit the `service.get('freeVersionLink', 'N/A')` line.


Options:
    <framework-slug>                                      Which iteration of G-Cloud to target. Use g-cloud-x format

    [--stage=STAGE]                                       Stage to target

    [--output-folder=OUTPUT]                              Folder in which the reports should go

    -h, --help                                            Show this screen

"""
import sys
import csv
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
    framework_slug = arguments['<framework-slug>']
    OUTPUT_DIR = arguments['--output-folder'] or '.'
    OUTPUT_FILENAME_PREFIX = 'service-free-trial-link'

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Set defaults, instantiate clients
    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token('api', stage)
    )

    services = data_api_client.find_services_iter(framework=f'{framework_slug}', status='published')

    headers = [
        'Supplier ID', 'Supplier Name', 'Service ID', 'Service Name', 'Lot', 'Free trial link'
    ]

    with open(
        os.path.join(OUTPUT_DIR, f'{OUTPUT_FILENAME_PREFIX}-{framework_slug}.csv'), 'w', newline=''
    ) as f:
        writer = csv.writer(f, delimiter=',', quotechar='"')
        writer.writerow(headers)

        for service in services:
            if service.get('freeVersionLink') == "N/A":
                row = [
                    str(service['supplierId']),
                    service.get('id'),
                    service.get('serviceName'),
                    service.get('lotSlug'),
                    service.get('freeVersionLink', 'N/A')
                ]
                writer.writerow(row)
