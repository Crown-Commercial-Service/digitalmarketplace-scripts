"""

Usage:
    scripts/generate_framework_agreements.py <lots_file> <declaration_file> <output_dir> <framework_form>

Example:
    ./generate_framework_agreements.py lots.csv declarations.csv pdf-outputs ../empty-framework.pdf
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.generate_framework_agreements import check_lots_csv, read_csv, \
    check_declarations_csv, build_framework_agreements

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

    build_framework_agreements(supplier_declarations,
                               supplier_lots,
                               arguments['<output_dir>'],
                               arguments['<framework_form>'])
    sys.exit("Success")
