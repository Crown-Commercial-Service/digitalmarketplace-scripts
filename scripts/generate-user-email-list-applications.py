"""
Generate a list of users that have applied to a given framework.
This is to be run after a framework has been closed.

Usage:
    scripts/generate-user-email-list-applications.py
    <data_api_url> <data_api_token>
    [--framework_slug=<framework_slug>] [--filename=<filename>] [--on_framework] [--agreement_not_returned]
"""
import sys
sys.path.insert(0, '.')

import six
from docopt import docopt
from dmapiclient import DataAPIClient
from dmscripts.generate_user_email_list_applications import list_users


if __name__ == '__main__':
    arguments = docopt(__doc__)

    data_api_client = DataAPIClient(arguments['<data_api_url>'], arguments['<data_api_token>'])
    output = open(arguments.get('--filename'), 'w+') if arguments.get('--filename') else sys.stdout
    on_framework = True if arguments.get('--on_framework') else None

    framework_slug = 'g-cloud-7'
    if isinstance(arguments.get('--framework_slug'), six.string_types):
        framework_slug = arguments.get('--framework_slug')

    agreement_returned = False if arguments.get('--agreement_not_returned') else None

    list_users(data_api_client, output, framework_slug, on_framework, agreement_returned)
