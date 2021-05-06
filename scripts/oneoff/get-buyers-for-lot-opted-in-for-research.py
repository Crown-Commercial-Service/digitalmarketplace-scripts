#!/usr/bin/env python3
"""
The logic in this script was copied from download_buyers_for_user_research in the admin frontend. It's been modified to
filter for users who've created a brief for a particular lot.

Usage:
    scripts/oneoff/get-buyers-for-lot-opted-in-for-research.py <stage> <output_file> [options]

Options:
    --lot=<lot>              Lot to filter for [default: digital-specialists]
"""

import csv
from docopt import docopt
import sys

from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage


sys.path.insert(0, ".")

from dmscripts.helpers import logging_helpers
from dmscripts.helpers.auth_helpers import get_auth_token


logger = logging_helpers.configure_logger()


if __name__ == "__main__":
    arguments = docopt(__doc__)

    stage = arguments["<stage>"]
    output_file = arguments["<output_file>"]
    lot = arguments["--lot"]

    data_api_client = DataAPIClient(
        get_api_endpoint_from_stage(stage), get_auth_token("api", stage)
    )

    users = [
        user
        for user in data_api_client.find_users_iter(
            role="buyer", user_research_opted_in=True
        )
        if any(data_api_client.find_briefs_iter(user_id=user["id"], lot=lot))
    ]

    with open(output_file, "w") as f:
        writer = csv.DictWriter(f, fieldnames=("email address", "name"))
        writer.writeheader()
        for user in users:
            writer.writerow(
                {"email address": user["emailAddress"], "name": user["name"]}
            )
