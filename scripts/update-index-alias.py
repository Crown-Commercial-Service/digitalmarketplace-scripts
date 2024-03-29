#!/usr/bin/env python3
"""
A script to update the elasticsearch index an alias is associated with.

Stage is an optional argument. If left as its default, 'development', the auth tokens will be set without needing to
access the credentials repo.

If an index is found to already be using the alias <alias>, that index is assigned the alias <alias>-old. If an index is
found to exist using *that* alias (<alias>-old), it is either deleted or simply has its alias removed according to
the --delete-old-index option. This way, routine use of this option should lead to only two copies of any particular
index being kept at once: <alias> and <alias>-old.

Usage:
scripts/update-index-alias.py <alias> <target> <search-api-endpoint> [options]

Options:
    --stage=stage               The stage being updated [default: development]
    --delete-old-index=yes/no   Whether to delete the index losing its alias [default: no]
"""
import sys
import json
from distutils.util import strtobool
import requests
from requests.exceptions import HTTPError
from docopt import docopt

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token


def update_index_alias(alias, target, stage, endpoint, delete_old_index):
    auth_token = 'myToken' if stage == 'development' else get_auth_token('search_api', stage)
    headers = {
        'Authorization': "Bearer {}".format(auth_token),
        'Content-type': 'application/json'
    }
    alias_old = "{}-old".format(alias)

    current_aliased_index = _get_index_from_alias(alias, endpoint)
    old_aliased_index = _get_index_from_alias(alias_old, endpoint)

    _apply_alias_to_index(alias, target, endpoint, headers)

    if current_aliased_index:
        _apply_alias_to_index(alias_old, current_aliased_index, endpoint, headers)

    if old_aliased_index and delete_old_index:
        _delete_index(old_aliased_index, endpoint, auth_token)


def _get_index_from_alias(alias, endpoint):
    status_url = "{}/_status".format(endpoint)

    response = requests.get(status_url)
    _check_response_status(response, 'fetching indexes')

    all_indexes = json.loads(response.content)['es_status']
    index_name = [index for index in all_indexes.keys() if alias in all_indexes[index]['aliases']]

    current_indexes_and_aliases = {k: {"aliases": v['aliases']} for k, v in all_indexes.items()}
    print("Current indexes and aliases:")
    print('\n'.join('{} has aliases {}'.format(k, v['aliases']) for k, v in current_indexes_and_aliases.items()))

    if not index_name:
        print("No index found with the '{}' alias".format(alias))
        return None

    return index_name[0]


def _apply_alias_to_index(alias, target, endpoint, headers):
    url = "{}/{}".format(endpoint, alias)
    data = {'type': 'alias', 'target': "{}".format(target)}

    response = requests.put(url, headers=headers, json=data)
    _check_response_status(response, "updating alias '{}' to point at the '{}' index.".format(alias, target))


def _delete_index(index, endpoint, auth_token):
    headers = {
        'Authorization': "Bearer {}".format(auth_token),
    }

    response = requests.delete("{}/{}".format(endpoint, index), headers=headers)
    _check_response_status(response, "deleting the '{}' index".format(index))


def _check_response_status(response, action):
    try:
        response.raise_for_status()
    except HTTPError as e:
        print("HTTPError {}: {}".format(e.args[0], action))
        sys.exit(1)
    except Exception as e:
        print("Error {}: {}".format(e, action))
        sys.exit(2)

    print("Success {}".format(action))


if __name__ == "__main__":
    arguments = docopt(__doc__)
    alias = arguments['<alias>']
    target = arguments['<target>']
    endpoint = arguments['<search-api-endpoint>']
    stage = arguments['--stage']
    delete_old_index = strtobool(arguments['--delete-old-index'])
    update_index_alias(alias, target, stage, endpoint, delete_old_index)
