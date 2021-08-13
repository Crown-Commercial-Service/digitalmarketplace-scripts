#!/usr/bin/env python3
"""
Populate your local database with enough randomly generated data to run the DMp using the API. Currently only creates a
single buyer user account.

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

    # Applying only the database migrations to an empty database creates several frameworks in various states. Set
    # them all to expired before we start adding new data
    set_all_frameworks_to_expired(data)

    open_gcloud_12(data)

    create_buyer_email_domain_if_not_present(data, "user.marketplace.team")

    generate_user(data, "buyer")

    make_gcloud_12_live(data)

    print("Generation has been completed.")
