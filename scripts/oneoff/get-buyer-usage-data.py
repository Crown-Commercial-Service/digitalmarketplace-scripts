#!/usr/bin/env python3
"""
Get data on the number of direct award projects created with and without a reported outcome.

Usage:
    get-buyer-usage-data.py <stage> <since>

To respond to an ad-hoc request for data on buyer usage for G-Cloud.
"""

import itertools
import sys
from datetime import datetime

from docopt import docopt

from dmapiclient.data import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage

sys.path.insert(0, ".")

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.datetime_helpers import parse_datetime

if __name__ == "__main__":
    args = docopt(__doc__)

    stage = args["<stage>"]

    since_datetime: datetime = parse_datetime(args["<since>"])

    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token("api", stage),
    )

    all_projects_with_outcome = data_api_client.find_direct_award_projects_iter(
        latest_first=True, having_outcome=True, with_users=True
    )
    recent_projects_with_outcome = list(
        itertools.takewhile(
            lambda p: parse_datetime(p["createdAt"]) > since_datetime,
            all_projects_with_outcome,
        )
    )
    unique_user_with_outcome_count = len(
        {project["users"][0]["id"] for project in recent_projects_with_outcome}
    )

    all_projects_without_outcome = data_api_client.find_direct_award_projects_iter(
        latest_first=True, having_outcome=False, with_users=True
    )
    recent_projects_without_outcome = list(
        itertools.takewhile(
            lambda p: parse_datetime(p["createdAt"]) > since_datetime,
            all_projects_without_outcome,
        )
    )
    unique_user_without_outcome_count = len(
        {project["users"][0]["id"] for project in recent_projects_without_outcome}
    )

    print(
        f"{len(recent_projects_with_outcome)} direct award projects with an outcome since {since_datetime}, "
        f"created by {unique_user_with_outcome_count} unique users"
    )
    print(
        f"{len(recent_projects_without_outcome)} direct award projects without an outcome since {since_datetime}, "
        f"created by {unique_user_without_outcome_count} unique users"
    )
