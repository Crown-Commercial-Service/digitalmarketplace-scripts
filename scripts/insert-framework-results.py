"""
Takes a CSV file with rows in the format: Supplier ID, Supplier Name, Result
e.g:
123456, Supplier name 1, pass
123212, Supplier name 2, fail
234567, Supplier name 3, pass

Usage:
    scripts/insert-framework-results.py <framework_slug> <data_api_url> <data_api_token> <filename>
"""

import getpass
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmapiclient import DataAPIClient
from dmscripts.insert_framework_results import insert_results


if __name__ == '__main__':
    arguments = docopt(__doc__)

    client = DataAPIClient(arguments['<data_api_url>'], arguments['<data_api_token>'])
    output = sys.stdout
    framework_slug = arguments['<framework_slug>']
    filename = arguments['<filename>']
    user = getpass.getuser()

    insert_results(client, output, framework_slug, filename, user)
