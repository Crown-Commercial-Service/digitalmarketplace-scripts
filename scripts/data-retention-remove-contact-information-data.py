#!/usr/bin/env python3
"""
Our data retention policy is that suppliers with no users that still have personal data should have the personal data
stripped from their contact details.

This script is very simple and has not been upgraded to accept any arguments to prevent the possibility of accidental
deletion. If you are in doubt use the dry run option.

Usage: data-retention-remove-contact-information-data.py <stage> [--dry-run] [--verbose]

Options:
    --stage=<stage>                                       Stage to target

    --dry-run                                             List account that would have data stripped
    --verbose
    -h, --help                                            Show this screen

Examples:
    ./scripts/data-retention-remove-contact-information-data.py preview
    ./scripts/data-retention-remove-contact-information-data.py preview --dry-run --verbose

"""
import logging
import sys
from docopt import docopt
from itertools import groupby
from dmapiclient import DataAPIClient
from datetime import datetime

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers import logging_helpers
from dmutils.env_helpers import get_api_endpoint_from_stage


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

    users = sorted(data_api_client.find_users_iter(role='supplier'), key=lambda i: i['supplier']['supplierId'])
    users_by_supplier_id = groupby(users, lambda i: i['supplier']['supplierId'])

    for supplier_id, users in users_by_supplier_id:
        if all(user['personalDataRemoved'] for user in users):
            supplier = data_api_client.get_supplier(supplier_id)['suppliers']
            for contact_information in supplier['contactInformation']:
                if not contact_information['personalDataRemoved']:

                    logger.warn("""{}Removing contact information #{} data for supplier {}""".format(
                        prefix,
                        contact_information['id'],
                        supplier_id)
                    )
                    if not dry_run:
                        data_api_client.remove_contact_information_personal_data(
                            supplier['id'],
                            contact_information['id'],
                            'Data Retention Script {}'.format(datetime.now().isoformat())
                        )
