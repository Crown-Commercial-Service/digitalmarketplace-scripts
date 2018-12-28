"""
Generate a list of buyer users name and email address, optionally with a list of their requirements

Usage:
    scripts/generate-buyer-email-list.py <stage> [--briefs]
"""
from multiprocessing.pool import ThreadPool
import sys

sys.path.insert(0, '.')

from docopt import docopt
from dmapiclient import DataAPIClient
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.generate_buyer_email_list import list_buyers
from dmutils.env_helpers import get_api_endpoint_from_stage


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), get_auth_token('api', STAGE))
    output = sys.stdout
    include_briefs = bool(arguments.get('--briefs'))

    pool = ThreadPool(10)

    list_buyers(client, output, include_briefs, unordered_map_impl=pool.imap_unordered)
