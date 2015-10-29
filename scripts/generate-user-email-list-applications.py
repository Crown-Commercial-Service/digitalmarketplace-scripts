"""

Usage:
    scripts/generate-user-email-list-applications.py
    <data_api_url> <data_api_token> [--filename=<filename>] [--on_framework] [--agreement_not_returned]
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmutils.apiclient import DataAPIClient
from dmscripts.generate_user_email_list_applications import list_users


if __name__ == '__main__':
    arguments = docopt(__doc__)

    data_api_client = DataAPIClient(arguments['<data_api_url>'], arguments['<data_api_token>'])
    output = open(arguments.get('--filename'), 'w+') if arguments.get('--filename') else sys.stdout
    framework_slug = 'g-cloud-7'
    on_framework = True if arguments.get('--on_framework') else None
    agreement_returned = False if arguments.get('--agreement_not_returned') else None

    list_users(data_api_client, output, framework_slug, on_framework, agreement_returned)
