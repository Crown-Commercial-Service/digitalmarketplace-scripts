#!/usr/bin/env python
"""
Our data retention policy is that users have accounts deactivated and personal data stripped after 3 years without
a login.

This script is very simple and has not been upgraded to accept any arguments to prevent the possibility of accidental
deletion. If you are in doubt use the dry run option.

Usage: data-retention-remove-user-data.py <stage> [--dry-run] [--verbose]

Options:
    --stage=<stage>                                       Stage to target

    --dry-run                                             List account that would have data stripped
    --verbose
    -h, --help                                            Show this screen

Examples:
    ./scripts/data-retention-remove-user-data.py preview
    ./scripts/data-retention-remove-user-data.py preview --dry-run --verbose

"""
import logging
import sys
from datetime import datetime, timedelta
from docopt import docopt

from dmapiclient import DataAPIClient

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers import logging_helpers


if __name__ == "__main__":
    arguments = docopt(__doc__)

    # Get script arguments
    stage = arguments['<stage>']

    dry_run = arguments['--dry-run']
    verbose = arguments['--verbose']

    # Set defaults, instantiate clients
    prefix = '[DRY RUN]: ' if dry_run else ''
    logger = logging_helpers.configure_logger(
        {"dmapiclient": logging.INFO} if verbose else {"dmapiclient": logging.WARN}
    )
    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token('api', stage)
    )
    cutoff_date = datetime.now() - timedelta(days=365 * 3)

    all_users = list(data_api_client.find_users_iter(personal_data_removed=False))

    for user in all_users:
        last_logged_in_at = datetime.strptime(user['loggedInAt'], '%Y-%m-%dT%H:%M:%S.%fZ')
        if last_logged_in_at < cutoff_date and not user['personalDataRemoved']:
            logger.warn(
                f"{prefix}Removing personal data for user: {user['id']}"
            )
            if not dry_run:
                data_api_client.remove_user_personal_data(
                    user['id'],
                    'Data Retention Script {}'.format(datetime.now().isoformat())
                )
