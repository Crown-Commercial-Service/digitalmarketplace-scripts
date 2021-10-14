#!/usr/bin/env python
"""
Find out what proportion of services for a framework were copied from a previous framework.

Usage:
    scripts/oneoff/how_many_copied.py <stage> <framework>
"""


import sys

from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt
from dmapiclient import DataAPIClient

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token


if __name__ == '__main__':
    arguments = docopt(__doc__)

    stage = arguments['<stage>']
    framework = arguments['<framework>']

    data_api_client = DataAPIClient(get_api_endpoint_from_stage(stage), get_auth_token('api', stage))

    total = 0
    copied = 0

    for draft in data_api_client.find_draft_services_by_framework_iter(framework, status='submitted'):
        total += 1
        if "copiedFromServiceId" in draft:
            copied += 1

    print(f"Total: {total}")
    print(f"Copied: {copied} ({copied/total:%})")
