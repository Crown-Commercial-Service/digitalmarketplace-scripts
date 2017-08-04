#!/usr/bin/env python
"""
A script to update the search index an alias is assoiciated with.

To delete old indexes (those with no alias), set --delete-old-indexes=yes

Usage:
scripts/update-index-alias.py <alias> <target> <stage> <search-api-endpoint> [options]

Options:
    --delete-old-indexes=<delete-old-indexes>  [default: ]
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
    url = "https://{}/{}".format(endpoint, alias)
    auth_token = _get_auth_token(stage)
    headers = {
        'Authorization': "Bearer {}".format(auth_token),
        'Content-type': 'application/json'
    }
    data = {'type': 'alias', 'target': "{}".format(target)}

    response = requests.put(url, headers=headers, json=data)

    try:
        response.raise_for_status()
    except HTTPError as e:
        print("HTTPError updating alias: {}".format(e.args[0]))
        sys.exit(1)
    except Exception as e:
        print("Error updating alias: {}".format(e))
        sys.exit(2)

    print('Successfully updated alias')

    if delete_old_indexes == 'yes':
        _delete_old_indexes(endpoint, auth_token)


def _get_auth_token(stage):
    DM_CREDENTIALS_REPO = os.environ.get('DM_CREDENTIALS_REPO')
    creds = subprocess.check_output([
        "{}/sops-wrapper".format(DM_CREDENTIALS_REPO),
        "-d",
        "{}/vars/{}.yaml".format(DM_CREDENTIALS_REPO, stage)
    ])
    return yaml.load(creds)['search_api']['auth_tokens'][2]


def _delete_old_indexes(endpoint, auth_token):
    status_url = "https://{}/_status".format(endpoint.replace('search-api', 'www'))
    response = requests.get(status_url)

    try:
        response.raise_for_status()
    except HTTPError as e:
        print("HTTPError fetching indexes: {}".format(e.args[0]))
        sys.exit(1)
    except Exception as e:
        print("Error fetching indexes: {}".format(e))
        sys.exit(2)

    current_indexes = json.loads(response.content)['search_api_status']['es_status']
    indexes_to_delete = [
        index for index in current_indexes.keys() if not current_indexes[index]['aliases']
    ]

    if len(indexes_to_delete) >= len(current_indexes):
        print('Error: Can not delete all indexes')
        sys.exit(3)

    base_url = "https://{}/{}"
    headers = {
        'Authorization': "Bearer {}".format(auth_token),
    }
    for index in indexes_to_delete:
        response = requests.delete(base_url.format(endpoint, index), headers=headers)

        try:
            response.raise_for_status()
        except HTTPError as e:
            print("HTTPError deleting index {}: {}".format(index, e.args[0]))
            sys.exit(1)
        except Exception as e:
            print("Error deleting index {}: {}".format(index, e))
            sys.exit(2)

    print('Completed deleting indexes')


if __name__ == "__main__":
    arguments = docopt(__doc__)
    alias = arguments['<alias>']
    target = arguments['<target>']
    stage = arguments['<stage>']
    endpoint = arguments['<search-api-endpoint>']
    delete_old_indexes = arguments['--delete-old-indexes']
    update_index_alias(alias, target, stage, endpoint, delete_old_indexes)
