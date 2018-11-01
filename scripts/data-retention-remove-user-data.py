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
from docopt import docopt

from dmapiclient import DataAPIClient

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers import logging_helpers
from dmutils.env_helpers import get_api_endpoint_from_stage
from dmscripts.data_retention_remove_user_data import main


if __name__ == "__main__":
    arguments = docopt(__doc__)

    # Get script arguments
    stage = arguments['<stage>']

    dry_run = arguments['--dry-run']
    verbose = arguments['--verbose']

    # Set defaults, instantiate clients
    logger = logging_helpers.configure_logger(
        {"dmapiclient": logging.INFO} if verbose else {"dmapiclient": logging.WARN}
    )
    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token('api', stage)
    )
    main(data_api_client, logger, dry_run)
