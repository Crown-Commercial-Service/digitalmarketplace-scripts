#!/usr/bin/env python3

"""Export services as a CSV

Outputs a CSV of services for a framework lot

Usage: scripts/export-services-by-lot.py <stage> <framework> <lot_slug>

Example
    scripts/oneoff/export-services-by-lot.py preview g-cloud-11 cloud-hosting
"""

import csv
import itertools
import sys

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt
from dmapiclient import DataAPIClient


if __name__ == '__main__':
    arguments = docopt(__doc__)

    stage = arguments['<stage>']
    framework = arguments['<framework>']
    lot_slug = arguments['<lot_slug>']

    data_api_client = DataAPIClient(get_api_endpoint_from_stage(stage), get_auth_token('api', stage))
    filename = f'{framework}_{lot_slug}.csv'

    def get_iterator():
        return data_api_client.find_services_iter(framework=framework, lot=lot_slug, status='published')

    # Services contain different keys, take a bunch and find all the unique keys
    services_slice = itertools.islice(get_iterator(), 500)
    keys = list(map(lambda s: s.keys(), services_slice))
    unique_keys = set(itertools.chain(*keys))

    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=unique_keys)
        writer.writeheader()
        writer.writerows(get_iterator())

    print(f"Outputted {filename}")
