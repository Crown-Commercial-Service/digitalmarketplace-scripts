#!/usr/bin/env python
"""Export G-Cloud 8 supplier information for evaluation

Produces three files;
 - successful.csv containing suppliers that submitted at least one service and answered
   all mandatory and discretionary declaration questions correctly.
 - failed.csv containing suppliers that either failed to submit any services or answered
   some of the mandatory declaration questions incorrectly.
 - discretionary.csv containing suppliers that submitted at least one service and answered
   all mandatory declaration questions correctly but answered some discretionary questions
   incorrectly.

Usage:
    scripts/export-g8-suppliers.py [-h] <stage> <api_token> <content_path> <output_dir> [<supplier_id_file>]

Options:
    -h --help
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.env import get_api_endpoint_from_stage
from dmscripts.export_g8_suppliers import export_suppliers
from dmapiclient import DataAPIClient
from dmutils.content_loader import ContentLoader


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    API_TOKEN = arguments['<api_token>']
    CONTENT_PATH = arguments['<content_path>']
    OUTPUT_DIR = arguments['<output_dir>']

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), API_TOKEN)
    content_loader = ContentLoader(CONTENT_PATH)

    supplier_id_file = arguments['<supplier_id_file>']
    if supplier_id_file:
        with open(arguments['<supplier_id_file>'], 'r') as f:
            supplier_ids = map(int, filter(None, [l.strip() for l in f.readlines()]))
    else:
        supplier_ids = None

    export_suppliers(client, content_loader, OUTPUT_DIR, supplier_ids)
