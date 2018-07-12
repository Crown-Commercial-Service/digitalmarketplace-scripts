#!/usr/bin/env python
"""Migrate supplier trading status to more restricted answer set

We currently have a large number of possible values that suppliers can select to describe their trading status, and if
they do not match one that we define, they can enter a freetext description. After moving this question from the
declaration to the account level, we are restricting the number of options they can provide and removing the freetext
box in place of just 'other'.

If we cannot exactly match up options, we will drop the data altogether, which will force the supplier to provide it
again. This is because it feels safer to do this than to incorrectly change a supplier's trading status. We also have
an extra option defined that was not available before, so suppliers without a clear state should have this option
clearly presented to them.

See: https://trello.com/c/Wvvtb1yW/52

Usage:
    ./scripts/oneoff/migrate-supplier-trading-status.py <stage> [--dry-run]
"""
import sys
sys.path.insert(0, '.')

import backoff
import getpass
import requests
from docopt import docopt
from dmapiclient import DataAPIClient, HTTPError
from dmapiclient.errors import HTTPTemporaryError
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage


NEW_TRADING_STATUS_MAPPING = {
    'limited company': 'limited company (LTD)',
    'limited liability company': 'limited liability company (LLC)',
    'public limited company': 'public limited company (PLC)',
    'limited liability partnership': 'limited liability partnership (LLP)',
    'sole trader': 'sole trader',
}

_backoff_wrap = backoff.on_exception(
    backoff.expo,
    (HTTPError, HTTPTemporaryError, requests.exceptions.ConnectionError, RuntimeError),
    max_tries=5,
)


def migrate_trading_statuses(client, dry_run):
    prefix = '[DRY RUN]: ' if dry_run else ''
    success_counter, failure_counter = 0, 0

    print(f'{prefix}Retrieving suppliers from API ...')
    for i, supplier in enumerate(client.find_suppliers_iter()):
        mapped_trading_status = NEW_TRADING_STATUS_MAPPING.get(supplier.get('tradingStatus'), None)

        if not dry_run:
            try:
                _backoff_wrap(
                    lambda: client.update_supplier(
                        supplier_id=supplier['id'],
                        supplier={'tradingStatus': mapped_trading_status},
                        user=f'{getpass.getuser()} (migrate trading status script)',
                    )
                )()
                success_counter += 1

            except HTTPError as e:
                print(f"{prefix}Error updating supplier {supplier['id']}: {e.message}")
                failure_counter += 1

        if i % 100 == 0:
            print(f'{prefix}{i} suppliers processed ...')

    print(f'{prefix}Finished processing {i} suppliers.')

    print(f"{prefix}Succssfully updated: {success_counter}")
    print(f"{prefix}Failed to update: {failure_counter}")


if __name__ == '__main__':
    arguments = docopt(__doc__)

    stage = arguments['<stage>']
    dry_run = arguments['--dry-run']
    api_url = get_api_endpoint_from_stage(stage)

    migrate_trading_statuses(DataAPIClient(api_url, get_auth_token('api', stage)), dry_run)
