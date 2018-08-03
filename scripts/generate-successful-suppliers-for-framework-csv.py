#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate a CSV listing all suppliers who were successfully awarded onto a framework with the lots that they were
successful on. This CSV is published as an update communication through the Digital Marketplace when the framework
is awarded (i.e. when standstill ends).

Usage:
    scripts/generate-successful-suppliers-for-framework-csv.py <framework_slug> <stage> <filename>

Example:
    scripts/generate-successful-suppliers-for-framework-csv.py g-cloud-10 production g-cloud-10-successful-suppliers.csv
"""
import argparse
import csv
import sys

from dmapiclient import DataAPIClient

sys.path.insert(0, '.')

from dmscripts.helpers import logging_helpers
from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage

if __name__ == "__main__":
    logger = logging_helpers.configure_logger()

    parser = argparse.ArgumentParser()
    parser.add_argument('framework_slug', type=str, help='Which framework to generate successful supplier listing for.')
    parser.add_argument('stage', default='development', choices=['development', 'preview', 'staging', 'production'],
                        help="Which stage's API to communicate with.")

    args = parser.parse_args()

    FILENAME = f'{args.framework_slug}-all-successful-suppliers.csv'

    client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(args.stage),
        auth_token=get_auth_token('api', args.stage)
    )

    logger.info('Retrieving framework ...')
    all_lot_names = [lot['name'] for lot in client.get_framework(args.framework_slug)['frameworks']['lots']]
    map_suppliers_to_lots = {}

    logger.info('Looking up supplier services ...')
    all_framework_services = client.find_services_iter(framework=args.framework_slug)
    for service in all_framework_services:
        if service['supplierId'] not in map_suppliers_to_lots:
            map_suppliers_to_lots[service['supplierId']] = {'name': service['supplierName'], 'lots': set()}

        map_suppliers_to_lots[service['supplierId']]['lots'].add(service['lotName'])

    with open(FILENAME, 'w') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Supplier'] + all_lot_names)

        sorted_suppliers = (x for x in sorted(map_suppliers_to_lots.values(), key=lambda x: x['name'].lower()))
        writer.writerows(
            (
                [x['name']] + ['Yes' if lot_name in x['lots'] else '-' for lot_name in all_lot_names]
                for x in
                sorted_suppliers
            )
        )

    logger.info(f'Finished writing successful suppliers and lots to {FILENAME}')
