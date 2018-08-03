#!/usr/bin/env python
"""
Script to fetch application statistics for a framework from the API and push them to the Performance Platform.

Usage:
    scripts/send-stats-to-performance-platform.py <framework_slug> <stage> <pp_bearer> <pp_service> (--day | --hour)
"""
import sys

from docopt import docopt

from dmapiclient import DataAPIClient

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.send_stats_to_performance_platform import send_framework_stats
from dmutils.env_helpers import get_api_endpoint_from_stage


if __name__ == "__main__":
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    FRAMEWORK_SLUG = arguments['<framework_slug>']
    PERIOD = 'day' if arguments['--day'] else 'hour'

    api_url = get_api_endpoint_from_stage(STAGE)
    client = DataAPIClient(api_url, get_auth_token('api', STAGE))

    ok = send_framework_stats(client, FRAMEWORK_SLUG, PERIOD, arguments['<pp_bearer>'], arguments['<pp_service>'])
    if not ok:
        sys.exit(1)
