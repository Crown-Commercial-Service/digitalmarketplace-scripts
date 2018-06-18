"""
Generate a list of buyer users name and email address, optionally with a list of their requirements

Usage:
    scripts/generate-buyer-email-list.py <stage> [--briefs]
"""
import sys

sys.path.insert(0, '.')

from docopt import docopt
from dmapiclient import DataAPIClient
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.generate_buyer_email_list import list_buyers


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), get_auth_token('api', STAGE))
    output = sys.stdout
    include_briefs = bool(arguments.get('--briefs'))

    list_buyers(client, output, include_briefs)
