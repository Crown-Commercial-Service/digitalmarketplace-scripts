#!/usr/bin/env python3
"""
Remove a user's personal information from the Digital Marketplace.

This script should be run in response to a user requesting that we delete their personal information. It removes their
data from both our database and mailchimp.

Usage:
    scripts/remove-user-personal-information.py <stage> <mailchimp_api_key> <mailchimp_username> <user_email> [options]

Options:
    --dry-run                                             List account that would have data stripped
    --verbose
    -h, --help                                            Show this screen
"""
import logging
import sys
from docopt import docopt

from dmapiclient import DataAPIClient

sys.path.insert(0, ".")

from dmutils.email.dm_mailchimp import DMMailChimpClient
from dmutils.env_helpers import get_api_endpoint_from_stage

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers import logging_helpers
from dmscripts.data_retention_remove_user_data import remove_user_data

if __name__ == "__main__":
    arguments = docopt(__doc__)

    logger = logging_helpers.configure_logger(
        {"dmapiclient": logging.INFO}
        if arguments["--verbose"]
        else {"dmapiclient": logging.WARN}
    )

    stage = arguments["<stage>"]
    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token("api", stage),
    )
    dm_mailchimp_client = DMMailChimpClient(
        arguments["<mailchimp_username>"],
        arguments["<mailchimp_api_key>"],
        logger,
    )

    user = data_api_client.get_user(email_address=arguments["<user_email>"])
    if not user:
        raise Exception("User not found")

    remove_user_data(
        data_api_client=data_api_client,
        logger=logger,
        user=user["users"],
        dm_mailchimp_client=dm_mailchimp_client,
        dry_run=arguments["--dry-run"],
    )
