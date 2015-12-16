"""
NOTE: DESPITE APPEARANCES THIS IS NOT CURRENTLY A GENERAL PURPOSE SCRIPT.
      IT WILL ONLY WORK FOR FRAMEWORK=digital-outcomes-and-specialists LOT=digital-specialists

Usage:
    scripts/get-draft-details-for-lot.py <framework_slug> <lot_slug> <api_url> <api_token>

Example:
    ./get-draft-details-for-lot.py digital-outcomes-and-specialists digital-specialists http://localhost:5000 myToken
"""
import sys

sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.get_draft_details_for_lot import get_anonymised_services
from dmutils.apiclient import DataAPIClient

if __name__ == '__main__':

    arguments = docopt(__doc__)

    client = DataAPIClient(arguments['<api_url>'], arguments['<api_token>'])

    get_anonymised_services(client, arguments['<framework_slug>'], arguments['<lot_slug>'])

    sys.exit("Success")
