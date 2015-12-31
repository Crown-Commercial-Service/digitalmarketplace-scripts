"""

Usage:
    scripts/generate_framework_agreement-data.py <lots_file> <declaration_file> <output_dir> <api_url> <api_token>

Example:
    ./generate-framework-agreement-data.py lots.csv declarations.csv framework-outputs localhost:5000 myToken
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.generate_framework_agreement_data import check_lots_csv, read_csv, \
    check_declarations_csv, build_framework_agreements
from dmapiclient import DataAPIClient

if __name__ == '__main__':

    arguments = docopt(__doc__)

    supplier_lots = read_csv(arguments['<lots_file>'])
    supplier_declarations = read_csv(arguments['<declaration_file>'])

    # Remove first column titles row, if it exists
    if supplier_lots[0][0] == "Digital Marketplace ID":
        del supplier_lots[0]

    if supplier_declarations[0][0] == "Digital Marketplace ID":
        del supplier_declarations[0]

    lot_check = check_lots_csv(supplier_lots)
    if not lot_check[0]:
        sys.exit("Lots CSV is invalid: {}".format(lot_check[1]))

    declaration_check = check_declarations_csv(supplier_declarations)
    if not declaration_check[0]:
        sys.exit("Declarations CSV is invalid: {}".format(declaration_check[1]))

    client = DataAPIClient(arguments['<api_url>'], arguments['<api_token>'])

    build_framework_agreements(client,
                               supplier_declarations,
                               supplier_lots,
                               arguments['<output_dir>'])
    sys.exit("Success")
