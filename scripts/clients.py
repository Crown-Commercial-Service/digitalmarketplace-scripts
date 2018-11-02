#!/usr/bin/env python
"""Drops you into an IPython shell with the DataAPIClient and SearchAPIClient instantiated and targetting the specified
stage as `data` and `search` respectively.

Usage:
  clients.py [<stage>]

Example:
  ./clients.py
  ./clients.py development
  ./clients.py preview
  ./clients.py staging
"""

import argparse
import IPython
import sys

from dmapiclient import DataAPIClient, SearchAPIClient

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage


def clients_in_shell(stage):
    print('Retrieving credentials...')
    api_token = 'myToken'
    search_api_token = 'myToken'

    if stage != 'development':
        api_token = get_auth_token('api', stage),
        search_api_token = get_auth_token('search_api', stage)

    print('Creating clients...')
    data = DataAPIClient(get_api_endpoint_from_stage(stage), api_token)  # noqa
    search = SearchAPIClient(get_api_endpoint_from_stage(stage, app='search-api'), search_api_token)  # noqa

    print('Dropping into shell...')
    IPython.embed()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', default='development', help='The stage your clients should target',
                        choices=['development', 'preview', 'staging'], nargs='?')

    args = parser.parse_args()

    clients_in_shell(stage=args.stage.lower())
