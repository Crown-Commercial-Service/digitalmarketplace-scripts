#!/usr/bin/env python
"""Export supplier "about you" information for suppliers who applied to a framework

Currently will only work for the following frameworks:
  * g-cloud-8, g-cloud-9, g-cloud-10
  * digital-outcomes-and-specialists-2, digital-outcomes-and-specialists-3

Support for new frameworks needs to be explicitly added to the DECLARATION_FIELDS in
dmscripts/export_framework_applicant_details.py, though in the (far) future it would be nice if this information could
be pulled from the frameworks themselves provided the frameworks repo knew which fields classed as "about you".

Usage:
    scripts/export-framework-applicant-details.py <stage> <api_token> <framework_slug> <output_dir>

Example:
    scripts/export-framework-applicant-details.py dev myToken g-cloud-8 SCRIPT_OUTPUTS

"""
import datetime
import errno
import os
import sys

sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.export_framework_applicant_details import export_supplier_details
from dmapiclient import DataAPIClient


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    API_TOKEN = arguments['<api_token>']
    FRAMEWORK = arguments['<framework_slug>']
    OUTPUT_DIR = arguments['<output_dir>']

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), API_TOKEN)
    now = datetime.datetime.now()

    filename = FRAMEWORK + "-applicant_details-" + now.strftime("%Y-%m-%d_%H.%M-") + STAGE + ".csv"
    filepath = OUTPUT_DIR + os.sep + filename

    # Create output directory if it doesn't already exist
    if not os.path.exists(os.path.dirname(filepath)):
        try:
            os.makedirs(os.path.dirname(filepath))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    framework_lot_slugs = tuple([lot['slug'] for lot in client.get_framework(FRAMEWORK)['frameworks']['lots']])

    export_supplier_details(client, FRAMEWORK, filepath, framework_lot_slugs=framework_lot_slugs)
