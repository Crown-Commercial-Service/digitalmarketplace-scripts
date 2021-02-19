#!/usr/bin/env python3

"""Export brief responses as a CSV
Outputs a CSV of brief responses for a DOS framework

Usage: scripts/export_brief_responses.py <stage> <framework>

Example
    scripts/oneoff/export_brief_responses.py preview digital-outcomes-and-specialists-4
"""

import csv
import sys
from itertools import chain

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt
from dmapiclient import DataAPIClient


if __name__ == '__main__':
    arguments = docopt(__doc__)

    stage = arguments['<stage>']
    framework = arguments['<framework>']

    data_api_client = DataAPIClient(get_api_endpoint_from_stage(stage), get_auth_token('api', stage))
    filename = f'{framework}-brief-responses.csv'

    def get_iterator():
        # The default iterator does not include draft responses
        return chain(data_api_client.find_brief_responses_iter(framework=framework),
                           data_api_client.find_brief_responses_iter(framework=framework, status='draft'))


    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['briefId', 'status', 'supplierId', 'createdAt', 'submittedAt' ])
        writer.writeheader()
        for r in get_iterator():
            writer.writerow({'briefId': r.get('briefId'),
                            'status': r.get('status'),
                            'supplierId': r.get('supplierId'),
                            'createdAt': r.get('createdAt'),
                            'submittedAt': r.get('submittedAt')})

    print(f"Outputted {filename}")