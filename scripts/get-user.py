#!/usr/bin/env python3
"""Outputs details of a random active unlocked user with a given role.

For supplier users, providing additional <framework> and <lot> arguments allows
filtering by suppliers who have published services on the given framewok and lot.

Usage:
    get-user.py <role> [<framework>] [<lot>] [options]

    --api-url=<api_url>     API URL (overrides --stage)
    --api-token=<api_token  API Token (overrides --stage)
    --stage=<stage>         Stage to target; automatically derive/decrypt api url and token [default: development]

Example:
    ./get-user.py supplier g9 cloud-hosting
    ./get-user.py admin
    ./get-user.py --stage=preview supplier g-cloud-9
    ./get-user.py --stage=staging supplier dos2 digital-outcomes
"""

import sys

from docopt import docopt

sys.path.insert(0, '.')
from dmscripts.get_user import get_user

if __name__ == "__main__":
    arguments = docopt(__doc__)
    user = get_user(
        api_url=arguments['--api-url'],
        api_token=arguments['--api-token'],
        stage=arguments['--stage'],
        role=arguments['<role>'].lower(),
        framework=arguments['<framework>'].lower() if arguments['<framework>'] else None,
        lot=arguments['<lot>'].lower() if arguments['<lot>'] else None,
    )

    print("\n".join(": ".join(u) for u in [
        ('User role', user['role']),
        ('User name', user['name']),
        ('User email', user['emailAddress']),
    ]))
