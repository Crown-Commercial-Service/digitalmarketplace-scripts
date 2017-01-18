"""
For each Digital Outcomes and Specialists application this script:
 * gets the supplier declaration
 * checks whether it is a PASS, FAIL or DISCRETIONARY
 * gets the submitted drafts services and checks whether the lot-specific essential questions are PASS or FAIL
 * updates FAILED services to have `failed` status using the API
 * updates the `supplier_frameworks` entry for the application accordingly, using the API:
   - on_framework=true if declaration OK and at least one lot not `failed`
   - on_framework=false if declaration FAILed or there are no unfailed services
   - on_framework=NULL (no call to API) if declaration DISCRETIONARY and at least one lot not `failed`

Usage:
    scripts/insert-dos-framework-results.py <path_to_frameworks> <stage> --api-token=<data_api_token>

Example:
    python scripts/insert-dos-framework-results.py ../digitalmarkeplace-frameworks dev --api-token=myToken
"""
import sys
sys.path.insert(0, '.')

import getpass
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage

from docopt import docopt
from dmapiclient import DataAPIClient
from dmscripts.insert_dos_framework_results import process_dos_results
from dmutils.content_loader import ContentLoader

if __name__ == '__main__':
    arguments = docopt(__doc__)

    data_api_url = get_api_endpoint_from_stage(arguments['<stage>'], 'api')
    content_loader = ContentLoader(arguments['<path_to_frameworks>'])
    client = DataAPIClient(data_api_url, arguments['--api-token'])
    user = getpass.getuser()

    process_dos_results(client, content_loader, user)
