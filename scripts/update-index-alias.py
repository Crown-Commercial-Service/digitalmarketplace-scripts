#!/usr/bin/env python
"""
A script to update the search index an alias is assoiciated with.

To delete the old index (the index losing the '<alias>-old' alias), set --delete-old-index=yes

Usage:
scripts/update-index-alias.py <alias> <target> <stage> <search-api-endpoint> [options]

Options:
    --delete-old-index=<delete-old-index>  [default: no]
"""
import os
import sys
import subprocess
import yaml
import json
from distutils.util import strtobool
import requests
from requests.exceptions import HTTPError
from docopt import docopt


def update_index_alias(alias, target, stage, endpoint, delete_old_index):
    auth_token = _get_auth_token(stage)
    headers = {
        'Authorization': "Bearer {}".format(auth_token),
        'Content-type': 'application/json'
    }

    if delete_old_index:
        old_index_to_delete = _get_old_index_to_delete(alias, endpoint)

    _rename_current_alias_to_old(alias, endpoint, headers)

    if delete_old_index:
        _delete_old_index(old_index_to_delete, endpoint, auth_token)

    url = "https://{}/{}".format(endpoint, alias)
    data = {'type': 'alias', 'target': "{}".format(target)}

    response = requests.put(url, headers=headers, json=data)
    _check_response_status(response, 'updating alias')


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
    old_alias = "{}-old".format(alias)
    url = "https://{}/{}".format(endpoint, old_alias)
    data = {'type': 'alias', 'target': "{}".format(alias)}

    response = requests.put(url, headers=headers, json=data)

    _check_response_status(response, 'renaming old alias')


def _get_old_index_to_delete(alias, endpoint):
    status_url = "https://{}/_status".format(endpoint.replace('search-api', 'www'))

    response = requests.get(status_url)
    _check_response_status(response, 'fetching indexes')

    current_indexes = json.loads(response.content)['search_api_status']['es_status']
    old_index_to_delete = [
        index for index in current_indexes.keys() if "{}-old".format(alias) in current_indexes[index]['aliases']
    ][0]

    return old_index_to_delete


def _delete_old_index(old_index_to_delete, endpoint, auth_token):
    headers = {
        'Authorization': "Bearer {}".format(auth_token),
    }

    response = requests.delete("https://{}/{}".format(endpoint, old_index_to_delete), headers=headers)
    _check_response_status(response, "deleting {} index".format(old_index_to_delete))


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
    delete_old_index = strtobool(arguments['--delete-old-index'])
    update_index_alias(alias, target, stage, endpoint, delete_old_index)
