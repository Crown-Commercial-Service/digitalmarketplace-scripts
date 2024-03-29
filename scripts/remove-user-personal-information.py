#!/usr/bin/env python3
"""
Remove a user's personal information from the Digital Marketplace.

This script should be run in response to a user requesting that we delete their personal information. It removes their
data from both our database and mailchimp.

Usage:
    scripts/remove-user-personal-information.py <stage> <user_email> [options]

Options:
    --dry-run    List account that would have data stripped
    --verbose
    -h, --help   Show this screen
"""
import logging
import sys
from docopt import docopt

from dmapiclient import DataAPIClient

sys.path.insert(0, ".")

from dmutils.email.dm_mailchimp import DMMailChimpClient
from dmutils.env_helpers import get_api_endpoint_from_stage

from dmscripts.helpers.auth_helpers import get_auth_token, get_mailchimp_credentials
from dmscripts.helpers import logging_helpers
from dmscripts.data_retention_remove_user_data import remove_user_data, remove_user_from_mailchimp

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
    (username, api_key) = get_mailchimp_credentials(stage)
    dm_mailchimp_client = DMMailChimpClient(
        username,
        api_key,
        logger,
    )

    user = data_api_client.get_user(email_address=arguments["<user_email>"])
    if user:
        remove_user_data(
            data_api_client=data_api_client,
            logger=logger,
            user=user["users"],
            dry_run=arguments["--dry-run"],
        )
    else:
        logger.info("User does not have an account on the Digital Marketplace")
        user = {"users": {"emailAddress": arguments["<user_email>"], "id": "n/a"}}

    remove_user_from_mailchimp(
        dm_mailchimp_client=dm_mailchimp_client,
        logger=logger,
        user=user["users"],
        dry_run=arguments["--dry-run"]
    )
