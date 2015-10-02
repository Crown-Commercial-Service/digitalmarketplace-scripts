"""

Usage:
    scripts/generate-user-email-list.py <data_api_url> <data_api_token> [--framework=<slug>] [--status]
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmutils.apiclient import DataAPIClient
from dmscripts.generate_user_email_list import list_users


if __name__ == '__main__':
    arguments = docopt(__doc__)

    client = DataAPIClient(arguments['<data_api_url>'], arguments['<data_api_token>'])
    output = sys.stdout
    framework_slug = arguments.get('--framework')
    include_status = bool(arguments.get('--status'))

    list_users(client, output, framework_slug, include_status)
