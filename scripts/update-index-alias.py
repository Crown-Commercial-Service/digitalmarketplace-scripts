#!/usr/bin/env python
"""
A script to update the search index an alias is assoiciated with.

To delete old indexes (those with no alias), set --delete-old-indexes=yes

Usage:
scripts/update-index-alias.py <alias> <target> <stage> <search-api-endpoint> [options]

Options:
    --delete-old-indexes=<delete-old-indexes>  [default: no]
"""
import os
import sys
import subprocess
import yaml
import json
import requests
from requests.exceptions import HTTPError
from docopt import docopt


def update_index_alias(alias, target, stage, endpoint, delete_old_indexes):
    auth_token = _get_auth_token(stage)
    headers = {
        'Authorization': "Bearer {}".format(auth_token),
        'Content-type': 'application/json'
    }

    _rename_current_alias_to_old(alias, endpoint, headers)

    url = "https://{}/{}".format(endpoint, alias)
    data = {'type': 'alias', 'target': "{}".format(target)}

    response = requests.put(url, headers=headers, json=data)
    _check_response_status(response, 'updating alias')

    if delete_old_indexes == 'yes':
        _delete_old_indexes(endpoint, auth_token)


def _get_auth_token(stage):
    DM_CREDENTIALS_REPO = os.environ.get('DM_CREDENTIALS_REPO')
    creds = subprocess.check_output([
        "{}/sops-wrapper".format(DM_CREDENTIALS_REPO),
        "-d",
        "{}/vars/{}.yaml".format(DM_CREDENTIALS_REPO, stage)
    ])
    auth_tokens = yaml.load(creds)['search_api']['auth_tokens']
    dev_token = [token for token in auth_tokens if token[0] == 'D']
    return dev_token[0]


def _rename_current_alias_to_old(alias, endpoint, headers):
    old_alias = "old-{}".format(alias)
    url = "https://{}/{}".format(endpoint, old_alias)
    data = {'type': 'alias', 'target': "{}".format(alias)}

    response = requests.put(url, headers=headers, json=data)

    _check_response_status(response, 'renaming old alias')


def _delete_old_indexes(endpoint, auth_token):
    status_url = "https://{}/_status".format(endpoint.replace('search-api', 'www'))

    response = requests.get(status_url)
    _check_response_status(response, 'fetching indexes')

    current_indexes = json.loads(response.content)['search_api_status']['es_status']
    indexes_to_delete = [
        index for index in current_indexes.keys() if not current_indexes[index]['aliases']
    ]

    if len(current_indexes) - len(indexes_to_delete) < 2:
        print('Error: Deleting too many indexes')
        sys.exit(3)

    base_url = "https://{}/{}"
    headers = {
        'Authorization': "Bearer {}".format(auth_token),
    }

    for index in indexes_to_delete:
        response = requests.delete(base_url.format(endpoint, index), headers=headers)
        _check_response_status(response, "deleting unaliased index {}".format(index))

    print('Completed deleting unaliased indexes')


def _check_response_status(response, action):
    try:
        response.raise_for_status()
    except HTTPError as e:
        print("HTTPError {}: {}".format(e.args[0], action))
        sys.exit(1)
    except Exception as e:
        print("Error {}: {}".format(e), action)
        sys.exit(2)

    print("Success {}".format(action))


if __name__ == "__main__":
    arguments = docopt(__doc__)
    alias = arguments['<alias>']
    target = arguments['<target>']
    stage = arguments['<stage>']
    endpoint = arguments['<search-api-endpoint>']
    delete_old_indexes = arguments['--delete-old-indexes']
    update_index_alias(alias, target, stage, endpoint, delete_old_indexes)
