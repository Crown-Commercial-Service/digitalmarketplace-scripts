#!/usr/bin/env python3
"""
N.B.: this is a work in progress with only few steps implemented.
The aim is to populate your local database with enough randomly generated data to run the DMp using the API.

Usage:
./scripts/generate-database-data.py
"""

import sys
from docopt import docopt
from dmapiclient import DataAPIClient

sys.path.insert(0, '.')
from dmscripts.generate_database_data import (
    open_gcloud_12,
    make_gcloud_12_live,
    create_buyer_email_domain_if_not_present,
    generate_user,
    set_all_frameworks_to_expired,
)
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.updated_by_helpers import get_user
from dmutils.env_helpers import get_api_endpoint_from_stage

STAGE = 'development'

if __name__ == "__main__":
    args = docopt(__doc__)

    print("Generating test data...")

    user = get_user()
    api_token = get_auth_token('api', STAGE)

    data = DataAPIClient(
        base_url=get_api_endpoint_from_stage(STAGE),
        auth_token=api_token,
        user=user,
    )

    # TODO complete the minimum set of data (see rest of this comment).
    # This document shows the data needed to make functional tests pass:
    # https://docs.google.com/document/d/1NE7owPrdUO3pW8Wri6sQu57LDsHH8CJd3kfMqXAd678
    # If you can't access the document, the steps are:
    # - add users: one for each type of admin, 2 buyers, 2 users per supplier
    #            Nice to have: add also the test logins the team knows about so that people can login to test
    # - add suppliers and services: 2 suppliers per lot, each supplier is on somewhere between 1 and all of the lots,
    #            1 service per lot per supplier on DOS frameworks, 2 services per lot per supplier on G-Cloud frameworks
    # - add opportunities: 1 closed per lot, 1 awarded per lot, 1 withdrawn per lot, 2 open per lot

    # Applying only the database migrations to an empty database creates several frameworks in various states. Set
    # them all to expired before we start adding new data
    set_all_frameworks_to_expired(data)

    open_gcloud_12(data)

    create_buyer_email_domain_if_not_present(data, "user.marketplace.team")

    generate_user(data, "buyer")

    make_gcloud_12_live(data)

    print("Generation has been completed.")
