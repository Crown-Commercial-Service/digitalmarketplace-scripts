"""
!!! Use this for ad-hoc updating of results for a known list of supplier IDs.

Takes a CSV file with rows in the format: Supplier ID, Supplier Name, Result
e.g:
123456, Supplier name 1, pass
123212, Supplier name 2, fail
234567, Supplier name 3, pass

The supplier name is cross-referenced against the supplier name in the Digital Marketplace for that supplier ID,
as a sanity check against sloppy CSV creation.
If the names don't match then the script will not update the framework status.

Usage:
    scripts/insert-framework-results.py <framework_slug> <stage> <data_api_token> <filename> [<user>]
"""

import getpass
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmapiclient import DataAPIClient
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.insert_framework_results import insert_results


if __name__ == '__main__':
    arguments = docopt(__doc__)

    client = DataAPIClient(get_api_endpoint_from_stage(arguments['<stage>']), arguments['<data_api_token>'])
    output = sys.stdout
    framework_slug = arguments['<framework_slug>']
    filename = arguments['<filename>']
    user = arguments['<user>'] or getpass.getuser()

    insert_results(client, output, framework_slug, filename, user)
