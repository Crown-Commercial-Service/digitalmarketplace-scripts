#!/usr/bin/env python
"""Export supplier information for a particular framework for evaluation

This can only be run *after* the on_framework flag has been set (e.g. by running mark-definite-framework-results.py)

Produces three files;
 - successful.csv containing suppliers that submitted at least one valid service and answered
   all mandatory and discretionary declaration questions correctly.
 - failed.csv containing suppliers that either failed to submit any valid services or answered
   some of the mandatory declaration questions incorrectly.
 - discretionary.csv containing suppliers that submitted at least one valid service and answered
   all mandatory declaration questions correctly but answered some discretionary questions
   incorrectly.

Usage:
    scripts/export-framework-results-reasons.py [-h] <stage> <api_token> <framework_slug> <content_path> <output_dir>
      <declaration_schema_path> [<supplier_id_file>]

Options:
    -h --help
"""
import json
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.helpers.env import get_api_endpoint_from_stage
from dmscripts.export_framework_results_reasons import export_suppliers
from dmapiclient import DataAPIClient
from dmcontent.content_loader import ContentLoader


if __name__ == '__main__':
    args = docopt(__doc__)

    client = DataAPIClient(get_api_endpoint_from_stage(args['<stage>']), args['<api_token>'])
    content_loader = ContentLoader(args['<content_path>'])

    declaration_definite_pass_schema = json.load(open(args["<declaration_schema_path>"], "r"))
    declaration_baseline_schema = \
        (declaration_definite_pass_schema.get("definitions") or {}).get("baseline")

    supplier_id_file = args['<supplier_id_file>']
    if supplier_id_file:
        with open(supplier_id_file, 'r') as f:
            supplier_ids = map(int, filter(None, [l.strip() for l in f.readlines()]))
    else:
        supplier_ids = None

    export_suppliers(
        client,
        args['<framework_slug>'],
        content_loader,
        args['<output_dir>'],
        declaration_definite_pass_schema,
        declaration_baseline_schema,
        supplier_ids
    )
