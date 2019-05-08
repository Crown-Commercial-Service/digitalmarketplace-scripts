#!/usr/bin/env python
"""
Script to fetch application statistics for a framework from the API and push them to the Performance Platform.

Usage:
    scripts/send-stats-to-performance-platform.py <framework_slug> <stage> <pp_service> (--day | --hour)
    [<pp_bearer>] [--dry-run]
"""
import sys

from docopt import docopt

from dmapiclient import DataAPIClient

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token, get_jenkins_env_variable_from_credentials
from dmscripts.send_stats_to_performance_platform import send_framework_stats
from dmutils.env_helpers import get_api_endpoint_from_stage


if __name__ == "__main__":
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    FRAMEWORK_SLUG = arguments['<framework_slug>']
    PERIOD = 'day' if arguments['--day'] else 'hour'
    DRY_RUN = arguments['--dry-run']

    if FRAMEWORK_SLUG.startswith('g-cloud'):
        token_group = 'g-cloud'
    else:
        token_group = 'digital-outcomes-specialists'  # That's how the token is stored :(

    api_url = get_api_endpoint_from_stage(STAGE)
    client = DataAPIClient(api_url, get_auth_token('api', STAGE))
    # Use the token if supplied, otherwise look in credentials
    pp_auth_token = arguments['<pp_bearer>'] or get_jenkins_env_variable_from_credentials(
        'performance_platform_bearer_tokens.{}'.format(token_group)
    )

    ok = send_framework_stats(client, FRAMEWORK_SLUG, PERIOD, pp_auth_token, arguments['<pp_service>'], dry_run=DRY_RUN)
    if not ok:
        sys.exit(1)
