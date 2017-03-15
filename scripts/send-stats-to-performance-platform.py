"""
Script to fetch application statistics for a framework from the API and push them to the Performance Platform.

Usage:
    scripts/send-stats-to-performance-platform.py <framework_slug> <stage> <api_token> <pp_bearer> (--day | --hour)
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt

from dmapiclient import DataAPIClient

from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.send_stats_to_performance_platform import send_framework_stats

if __name__ == "__main__":
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    FRAMEWORK_SLUG = arguments['<framework_slug>']
    PERIOD = 'day' if arguments['--day'] else 'hour'

    api_url = get_api_endpoint_from_stage(STAGE)
    client = DataAPIClient(api_url, arguments['<api_token>'])

    ok = send_framework_stats(client, FRAMEWORK_SLUG, PERIOD, arguments['<pp_bearer>'])
    if not ok:
        sys.exit(1)
