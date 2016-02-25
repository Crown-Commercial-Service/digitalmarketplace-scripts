#!/usr/bin/env python
"""Export DOS user research labs

Usage:
    scripts/export-dos-labs.py <stage> <api_token>
"""
import sys
sys.path.insert(0, '.')

from multiprocessing.pool import ThreadPool
import itertools

from docopt import docopt
from dmscripts.env import get_api_endpoint_from_stage
from dmscripts.export_dos_suppliers import find_suppliers, FRAMEWORK_SLUG, add_framework_info, add_draft_services
from dmapiclient import DataAPIClient

if sys.version_info[0] < 3:
    import unicodecsv as csv
else:
    import csv


def find_all_labs(client):
    pool = ThreadPool(20)
    records = find_suppliers(client, FRAMEWORK_SLUG)
    records = pool.imap(add_framework_info(client, FRAMEWORK_SLUG), records)
    records = filter(lambda record: record['onFramework'], records)
    records = pool.imap(add_draft_services(client, FRAMEWORK_SLUG), records)
    services = itertools.chain.from_iterable(record['services'] for record in records)
    services = filter(
        lambda record: record['lot'] == 'user-research-studios' and record['status'] == 'submitted',
        services)

    return services


def write_csv(services, filename):
    writer = None
    bad_fields = ['links']

    with open(filename, "w+") as f:
        for service in services:
            service = {key: value for key, value in service.items() if key not in bad_fields}
            if writer is None:
                writer = csv.DictWriter(f, fieldnames=sorted(service.keys()))
                writer.writeheader()
            writer.writerow(service)


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    API_TOKEN = arguments['<api_token>']

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), API_TOKEN)
    write_csv(find_all_labs(client), "output/dos-labs.csv")
