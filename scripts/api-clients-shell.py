#!/usr/bin/env python3
"""Drops you into an IPython shell with the DataAPIClient and SearchAPIClient instantiated and targetting the specified
stage as `data` and `search` respectively.

Usage:
  api-clients-shell.py [<stage>]

Optional:
  --api-url           Override the implicit API URL
  --api-token         Override for the API key (don't decrypt from dm-credentials)
  --search-api-url    Override the implicit SearchAPI URL
  --search-api-token  Override for the SearchAPI key (don't decrypt from dm-credentials)

Example:
  ./scripts/api-clients-shell.py
  ./scripts/api-clients-shell.py development
  ./scripts/api-clients-shell.py preview
  ./scripts/api-clients-shell.py staging
"""

import argparse
import IPython
import sys

from dmapiclient import DataAPIClient, SearchAPIClient

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage


data = None
search = None


def clients_in_shell(stage, api_url, api_token, search_api_url, search_api_token):
    global data, search

    print('Retrieving credentials...')
    api_token = api_token or get_auth_token('api', stage)
    search_api_token = search_api_token or get_auth_token('search_api', stage)

    print('Creating clients...')
    data = DataAPIClient(api_url or get_api_endpoint_from_stage(stage), api_token)  # noqa
    search = SearchAPIClient(search_api_url or get_api_endpoint_from_stage(stage, app='search-api'), search_api_token)  # noqa

    print('Dropping into shell...')
    IPython.embed()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', default='development', help='The stage your clients should target',
                        choices=['development', 'preview', 'staging', 'production'], nargs='?')

    parser.add_argument('--api-url', help='Override the implicit API URL', type=str)
    parser.add_argument('--api-token', help='Override for the API key (don\'t decrypt from dm-credentials)', type=str)

    parser.add_argument('--search-api-url', help='Override the implicit SearchAPI URL', type=str)
    parser.add_argument('--search-api-token',
                        help='Override for the SearchAPI key (don\'t decrypt from dm-credentials)', type=str)

    args = parser.parse_args()

    clients_in_shell(stage=args.stage.lower(), api_url=args.api_url, api_token=args.api_token,
                     search_api_url=args.search_api_url, search_api_token=args.search_api_token)
