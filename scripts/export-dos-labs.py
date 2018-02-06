#!/usr/bin/env python
"""

For a DOS-type framework this will export details of all "user-research-studios" services.

Usage:
    scripts/export-dos-labs.py <stage> <api_token> <framework_slug>
"""
import itertools
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmapiclient import DataAPIClient

from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers.framework_helpers import find_suppliers_with_details_and_draft_services
from dmscripts.export_dos_labs import append_contact_information_to_services

if sys.version_info[0] < 3:
    import unicodecsv as csv
else:
    import csv

REQUIRED_CONTACT_DETAILS_KEYS = ['email', 'contactName', 'phoneNumber']


def find_all_labs(client):
    records = find_suppliers_with_details_and_draft_services(client,
                                                             FRAMEWORK_SLUG,
                                                             lot="user-research-studios",
                                                             statuses="submitted"
                                                             )
    records = list(filter(lambda record: record['onFramework'], records))
    records = append_contact_information_to_services(records, REQUIRED_CONTACT_DETAILS_KEYS)
    services = itertools.chain.from_iterable(record['services'] for record in records)
    return services


def write_labs_csv(services, filename):
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
    FRAMEWORK_SLUG = arguments['<framework_slug>']

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), API_TOKEN)
    write_labs_csv(find_all_labs(client), "output/{}-labs.csv".format(FRAMEWORK_SLUG))
