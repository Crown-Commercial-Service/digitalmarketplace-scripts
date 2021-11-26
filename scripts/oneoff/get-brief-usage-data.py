#!/usr/bin/env python3
"""
Get data on the number of further competition projects started and published.

Usage:
    get-brief-usage-data.py <stage> <since>

To respond to an ad-hoc request for data on buyer usage for G-Cloud.
"""

import sys

from docopt import docopt

from dmapiclient.data import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage

sys.path.insert(0, ".")

from dmscripts.helpers.auth_helpers import get_auth_token

if __name__ == "__main__":
    args = docopt(__doc__)

    stage = args["<stage>"]
    since = args["<since>"]

    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token("api", stage),
    )

    created_briefs = [
        brief["users"][0]["id"]
        for brief in data_api_client.find_briefs_iter(
            with_users=True, status_date_filters={"created_after": since}
        )
    ]
    published_briefs = [
        brief["users"][0]["id"]
        for brief in data_api_client.find_briefs_iter(
            with_users=True, status_date_filters={"published_after": since}
        )
    ]
    # We can't filter for `awarded_after`, but this should be close enough
    awarded_briefs = [
        brief["users"][0]["id"]
        for brief in data_api_client.find_briefs_iter(
            with_users=True,
            status_date_filters={"closed_after": since},
            status="awarded",
        )
    ]

    print(
        f"{len(created_briefs)} opportunities created since {since} by {len(set(created_briefs))} unique users"
    )
    print(
        f"{len(published_briefs)} opportunities published since {since} by {len(set(published_briefs))} unique users"
    )
    print(
        f"{len(awarded_briefs)} opportunities awarded since {since} by {len(set(awarded_briefs))} unique users"
    )
