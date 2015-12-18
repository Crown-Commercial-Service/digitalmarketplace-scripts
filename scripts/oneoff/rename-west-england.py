"""Rename West England to South West England in DOS submissions

See: https://www.pivotaltracker.com/n/projects/997836/stories/110243076

Usage:
    scripts/oneoff/rename-west-england.py <stage> <api_token> [--dry-run]
"""
import sys
sys.path.insert(0, '.')

from multiprocessing.pool import ThreadPool
import itertools
import json
from docopt import docopt
from dmutils.apiclient import DataAPIClient
from dmscripts.env import get_api_endpoint_from_stage

OLD_LOCATION = "West England"
NEW_LOCATION = "South West England"


def get_location_keys(draft):
    return [key for key in draft.keys() if 'Location' in key]


def create_draft_getter(client):
    def get_drafts(supplier):
        drafts = []
        for draft in client.find_draft_services_iter(supplier['id'], framework='digital-outcomes-and-specialists'):
            location_keys = get_location_keys(draft)
            if any(OLD_LOCATION in draft[key] for key in location_keys):
                drafts.append(draft)
        return drafts

    return get_drafts


def get_all_drafts(client):
    pool = ThreadPool(25)
    return itertools.chain.from_iterable(pool.imap_unordered(
        create_draft_getter(client),
        client.find_suppliers_iter()
    ))


def get_location(location):
    return NEW_LOCATION if location == OLD_LOCATION else location


if __name__ == '__main__':
    arguments = docopt(__doc__)

    stage = arguments['<stage>']
    api_token = arguments['<api_token>']
    dry_run = arguments['--dry-run']

    api_url = get_api_endpoint_from_stage(stage)
    client = DataAPIClient(api_url, api_token)

    counter = 0
    for draft in get_all_drafts(client):
        for location_key in get_location_keys(draft):
            draft[location_key] = [
                get_location(location) for location in draft[location_key]
            ]
        counter += 1
        if not dry_run:
            client.update_draft_service(draft['id'], draft, "script", list(draft.keys()))

    print("Updated {}".format(counter))
