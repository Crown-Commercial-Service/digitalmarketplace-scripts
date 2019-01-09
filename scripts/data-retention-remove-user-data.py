#!/usr/bin/env python
"""
Our data retention policy is that users have accounts deactivated and personal data stripped after 3 years without
a login. This script not only does that but also removes any such users' email addresses from any of our mailing lists.

This script is simple and has deliberately been designed without many arguments to reduce the possibility of
accidental deletion. If you are in doubt use the dry run option.

Usage: data-retention-remove-user-data.py <stage> [options]

Options:
    --stage=<stage>                                       Stage to target
    --mailchimp-api-key=<mailchimp_api_key>               Mailchimp API key, omit to skip mailing list checks
    --mailchimp-username=<mailchimp_username>             Mailchimp username, omit to skip mailing list checks

    --dry-run                                             List account that would have data stripped
    --verbose
    -h, --help                                            Show this screen

Examples:
    ./scripts/data-retention-remove-user-data.py preview
    ./scripts/data-retention-remove-user-data.py preview --dry-run --verbose

"""
import logging
import sys
from docopt import docopt

from dmapiclient import DataAPIClient

sys.path.insert(0, '.')

from dmutils.email.dm_mailchimp import DMMailChimpClient
from dmutils.env_helpers import get_api_endpoint_from_stage

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers import logging_helpers
from dmscripts.data_retention_remove_user_data import data_retention_remove_user_data


if __name__ == "__main__":
    arguments = docopt(__doc__)

    # Get script arguments
    stage = arguments['<stage>']

    # Set defaults, instantiate clients
    logger = logging_helpers.configure_logger(
        {"dmapiclient": logging.INFO} if arguments['--verbose'] else {"dmapiclient": logging.WARN}
    )
    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token('api', stage),
    )

    if bool(arguments.get("<mailchimp_username>")) != bool(arguments.get("<mailchimp_api_key>")):
        raise TypeError(
            "Either both of '--mailchimp-api-key' and '--mailchimp-username' need to be specified or neither"
        )

    if arguments.get("<mailchimp_username>"):
        dm_mailchimp_client = DMMailChimpClient(
            arguments["<mailchimp_username>"],
            arguments["<mailchimp_api_key>"],
            logger,
        )
        logger.info("Using Mailchimp username %s for mailing list checks", repr(arguments["<mailchimp_username>"]))
    else:
        dm_mailchimp_client = None
        logger.warn("No Mailchimp credentials provided - skipping mailing list checks")

    data_retention_remove_user_data(
        data_api_client=data_api_client,
        logger=logger,
        dm_mailchimp_client=dm_mailchimp_client,
        dry_run=arguments['--dry-run'],
    )
