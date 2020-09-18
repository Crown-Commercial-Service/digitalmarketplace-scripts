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
  -r --read-only      Only allow access to API calls that read data

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


def _is_read_only(item):
    return item.startswith("get") or item.startswith("find")


class ReadOnlyDataAPIClient:
    def __init__(self, data_client):
        self._data = data_client

    def __getattr__(self, item: str):
        attr = getattr(self._data, item)

        if _is_read_only(item):
            return attr
        else:
            raise AttributeError(f"'{item}' is not a read-only attribute of '{self.__class__.__name__}'")

    def __dir__(self):
        return filter(_is_read_only, dir(self._data))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', default='development', help='The stage your clients should target',
                        choices=['development', 'preview', 'staging', 'production'], nargs='?')

    parser.add_argument('--api-url', help='Override the implicit API URL', type=str)
    parser.add_argument('--api-token', help='Override for the API key (don\'t decrypt from dm-credentials)', type=str)

    parser.add_argument('--search-api-url', help='Override the implicit SearchAPI URL', type=str)
    parser.add_argument('--search-api-token',
                        help='Override for the SearchAPI key (don\'t decrypt from dm-credentials)', type=str)
    parser.add_argument('--read-only', '-r',
                        help='Only allow access to API calls that read data', action='store_true')

    args = parser.parse_args()

    stage = args.stage.lower()

    print('Retrieving credentials...')
    api_token = args.api_token or get_auth_token('api', stage)
    search_api_token = args.search_api_token or get_auth_token('search_api', stage)

    print('Creating clients...')
    data = DataAPIClient(
        args.api_url or get_api_endpoint_from_stage(stage),
        api_token
    )
    search = SearchAPIClient(
        args.search_api_url or get_api_endpoint_from_stage(stage, app='search-api'),
        search_api_token
    )

    if args.read_only:
        data = ReadOnlyDataAPIClient(data)

    print('Dropping into shell...')
    IPython.start_ipython(argv=[], user_ns={"data": data, "search": search})
