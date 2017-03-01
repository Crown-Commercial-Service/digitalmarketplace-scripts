#!/usr/bin/env python
"""Export supplier "about you" information for suppliers who applied to a framework

Currently will only work for g-cloud-8 and digital-outcomes-and-specialists-2 framework_slugs. Support for specific
frameworks needs to be explicitly added to the LOTS and DECLARATION_FIELDS in
dmscripts/export_framework_applicant_details.py, though in the (far) future it would be nice if this information could
be pulled from the frameworks themselves provided the frameworks repo knew which fields classed as "about you".

Usage:
    scripts/export-framework-applicant-details.py <stage> <api_token> <framework_slug> [<output_dir>]

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

    filename = OUTPUT_DIR + os.sep if OUTPUT_DIR else ""
    filename = filename + FRAMEWORK + "-applicant_details-" + now.strftime("%Y-%m-%d_%H.%M-") + STAGE + ".csv"

    # Create output directory if it doesn't already exist
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    export_supplier_details(client, FRAMEWORK, filename)
