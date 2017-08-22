#!/usr/bin/env python
"""Outputs details of a random active unlocked user with a given role.

For supplier users, providing additional <framework> and <lot> arguments allows
filtering by suppliers who have published services on the given framewok and lot.

Usage:
    get-user.py <role> [<framework>] [<lot>] [options]

    --api-url=<api_url>  API URL [default: http://localhost:5000]
    --api-token=<api_token>  API token [default: myToken]

Example:
    ./get-user.py supplier g9 cloud-hosting
    ./get-user.py --api-url=localhost:5000 --api-token=myToken admin
    ./get-user.py --api-url=localhost:5000 --api-token=myToken supplier g-cloud-9
    ./get-user.py --api-url=localhost:5000 --api-token=myToken supplier dos2 digital-outcomes
"""

import random
import re
import sys

import dmapiclient
from docopt import docopt

sys.path.insert(0, '.')  # noqa


def get_full_framework_slug(framework):
    iteration = re.search('(\d+)', framework)
    if framework.startswith('g'):
        prefix = 'g-cloud'
    elif framework.startswith('d'):
        prefix = 'digital-outcomes-and-specialists'
    else:
        return framework

    if iteration:
        return "{}-{}".format(prefix, iteration.group(1))
    else:
        return prefix


def get_supplier_id(api_client, framework, lot):
    services = [
        s for s in api_client.find_services(framework=framework, lot=lot)['services']
        if s['status'] in ['published']
    ]

    if not services:
        print("No live services found for '{}' framework{}".format(
            framework, " and '{}' lot".format(lot) if lot else '')
        )
        sys.exit(1)

    return random.choice(services)['supplierId']


def get_random_user(api_client, role, supplier_id=None):
    return random.choice([
        u for u in api_client.find_users(role=role, supplier_id=supplier_id)['users']
        if u['active'] and not u['locked']
    ])


def get_user(api_url, api_token, role, framework, lot):
    api_client = dmapiclient.DataAPIClient(api_url, api_token)

    if role == 'supplier' and framework is not None:
        framework = get_full_framework_slug(framework)
        print('Framework: {}'.format(framework))
        if lot is not None:
            print('Lot: {}'.format(lot))
        supplier_id = get_supplier_id(api_client, framework, lot)
        print('Supplier id: {}'.format(supplier_id))
        return get_random_user(api_client, None, supplier_id)
    else:
        return get_random_user(api_client, role)


if __name__ == "__main__":
    arguments = docopt(__doc__)
    user = get_user(
        api_url=arguments['--api-url'],
        api_token=arguments['--api-token'],
        role=arguments['<role>'].lower(),
        framework=arguments['<framework>'].lower() if arguments['<framework>'] else None,
        lot=arguments['<lot>'].lower() if arguments['<lot>'] else None,
    )

    print("\n".join(": ".join(u) for u in [
        ('User role', user['role']),
        ('User name', user['name']),
        ('User email', user['emailAddress']),
    ]))
