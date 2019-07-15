#!/usr/bin/env python3
"""
Our data retention policy is that suppliers who fail to be accepted onto the framework have their declarations
removed immediately. This reduces the likelihood of commercially sensitive data being leaked in the event of a breach

This script is very simple and has not been upgraded to accept any arguments to prevent the possibility of accidental
deletion. If you are in doubt use the dry run option.

Usage: data-retention-remove-failed-suppliers-declarations.py <stage> <framework-slug> [--dry-run] [--verbose] [<user>]

Options:
    --stage=<stage>                                       Stage to target
    --framework-slug=<framework-slug>                     Framework to target

    --dry-run
    --verbose                                             List data that would have been stripped
    -h, --help                                            Show this screen
    <user>                                                The user who's running this script

Examples:
    ./scripts/data-retention-remove-failed-suppliers-declarations.py preview g-cloud-9
    ./scripts/data-retention-remove-failed-suppliers-declarations.py preview g-cloud-9 --dry-run --verbose

"""
import logging
import getpass
import sys
from docopt import docopt

from dmapiclient import DataAPIClient

sys.path.insert(0, '.')

logger = logging.getLogger("script")

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers import logging_helpers
from dmutils.env_helpers import get_api_endpoint_from_stage
from dmscripts.data_retention_remove_supplier_declarations import remove_unsuccessful_supplier_declarations


if __name__ == "__main__":
    arguments = docopt(__doc__)

    # Get script arguments
    stage = arguments['<stage>']

    dry_run = arguments['--dry-run']
    framework = arguments['<framework-slug>']
    verbose = arguments['--verbose']
    user = arguments['<user>'] or getpass.getuser()

    # Set defaults, instantiate clients
    logging_helpers.configure_logger(
        {"dmapiclient": logging.INFO} if verbose else {"dmapiclient": logging.WARN}
    )
    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token('api', stage)
    )
    remove_unsuccessful_supplier_declarations(
        data_api_client=data_api_client,
        logger=logger,
        dry_run=dry_run,
        framework_slug=framework,
        user=user
    )
