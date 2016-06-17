"""
For each G-Cloud 8 application this script:
 * gets the supplier declaration
 * checks whether it is a PASS, FAIL or DISCRETIONARY
 * updates the `supplier_frameworks` entry for the application accordingly, using the API:
   - on_framework=true if declaration OK and at least one completed service
   - on_framework=false if declaration FAILed or there are no completed services
   - on_framework=NULL (no call to API) if declaration DISCRETIONARY and at least one completed service

Usage:
    scripts/insert-g8-framework-results.py <stage> --api-token=<data_api_token>

Example:
    python scripts/insert-dos-framework-results.py dev --api-token=myToken
"""
import sys
sys.path.insert(0, '.')

import getpass
from dmscripts.env import get_api_endpoint_from_stage

from docopt import docopt
from dmapiclient import DataAPIClient
from dmscripts.insert_g8_framework_results import process_g8_results

if __name__ == '__main__':
    arguments = docopt(__doc__)

    data_api_url = get_api_endpoint_from_stage(arguments['<stage>'], 'api')
    client = DataAPIClient(data_api_url, arguments['--api-token'])
    user = getpass.getuser()

    process_g8_results(client, user)
