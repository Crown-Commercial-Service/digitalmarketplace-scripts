#!/usr/bin/env python3

"""Export brief responses as a CSV
Outputs a CSV of brief responses for a DOS framework

Usage: scripts/export_brief_responses.py <stage> <framework>

Example
    scripts/oneoff/export_brief_responses.py preview digital-outcomes-and-specialists-4
"""
from dmapiclient import DataAPIClient
from docopt import docopt
from dmutils.env_helpers import get_api_endpoint_from_stage
import sys
import csv
from itertools import chain

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token

if __name__ == '__main__':
    arguments = docopt(__doc__)

    stage = arguments['<stage>']
    framework = arguments['<framework>']

    data_api_client = DataAPIClient(get_api_endpoint_from_stage(stage), get_auth_token('api', stage))
    filename = f'data/{framework}-brief-responses.csv'

    def get_iterator(brief_id):
        # The default iterator does not include draft responses
        return chain(data_api_client.find_brief_responses_iter(brief_id=brief_id, framework=framework),
                     data_api_client.find_brief_responses_iter(brief_id=brief_id, framework=framework, status='draft'))

    with open(filename, 'w') as csvfile:
        fieldnames = ['briefId', 'status', 'supplierId', 'createdAt', 'submittedAt']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        total_number_of_briefs = data_api_client.find_briefs(framework=framework)['meta']['total']
        count = 0

        for brief in data_api_client.find_briefs_iter(framework=framework):
            count += 1
            brief_id = brief['id']

            for brief_response in get_iterator(brief_id):
                writer.writerow({field: brief_response.get(field) for field in fieldnames})

            print(f"Briefs exported: {count:04d}/{total_number_of_briefs}", end='\r')

    print(f"Briefs exported: {count}/{total_number_of_briefs}")
    print(f"Outputted {filename}")
