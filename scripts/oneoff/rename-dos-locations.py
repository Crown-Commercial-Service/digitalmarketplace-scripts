"""Rename location fields

Rename location fields for digital-outcomes and user-research-participants.

Usage:
    scripts/oneoff/rename-dos-locations.py <stage> <token> [--dry-run]
"""
import sys
sys.path.insert(0, '.')

from multiprocessing.pool import ThreadPool
import itertools
from docopt import docopt
from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage


def create_draft_getter(client):
    def get_drafts(supplier):
        for draft in client.find_draft_services_iter(supplier['id'], framework='digital-outcomes-and-specialists'):
            yield draft
    return get_drafts


def get_all_drafts(client):
    pool = ThreadPool(25)
    return itertools.chain.from_iterable(pool.imap_unordered(
        create_draft_getter(client),
        client.find_suppliers_iter()
    ))


if __name__ == "__main__":
    arguments = docopt(__doc__)

    stage = arguments['<stage>']
    api_token = arguments['<token>']
    dry_run = arguments['--dry-run']

    api_url = get_api_endpoint_from_stage(stage)
    client = DataAPIClient(api_url, api_token)

    counter = 0
    for draft in get_all_drafts(client):
        update = {}
        if "outcomesLocations" in draft:
            update["locations"] = draft["outcomesLocations"]
            update["outcomesLocations"] = None
        if "recruitLocations" in draft:
            if update:
                raise ValueError("draft {} has both outcomesLocations and recruitLocations".format(draft["id"]))
            update["locations"] = draft["recruitLocations"]
            update["recruitLocations"] = None

        if update:
            counter += 1

            update_reason = "rename locations: https://www.pivotaltracker.com/story/show/113271913"
            if dry_run:
                print("{} {}".format(draft["id"], update))
            else:
                client.update_draft_service(draft["id"], update, update_reason)

            if counter % 10 == 0:
                print("Updated {}".format(counter))

    print("DONE: {}".format(counter))
