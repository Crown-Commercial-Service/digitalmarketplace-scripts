#!/usr/bin/env python
"""Export supplier "about you" information for suppliers who applied to a framework.
   This report includes registered company information and contact details.

Usage:
    scripts/framework-applications/export-framework-applicant-details.py <stage> <framework_slug> <output_dir>

Options:
    --verbose                   Show debug log messages
    -h, --help                  Show this screen

Example:
    scripts/framework-applications/export-framework-applicant-details.py dev g-cloud-12 SCRIPT_OUTPUTS

"""
import datetime
import errno
from multiprocessing.pool import ThreadPool
import os
import sys

sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.logging_helpers import configure_logger, get_logger
from dmscripts.helpers.logging_helpers import INFO as loglevel_INFO, DEBUG as loglevel_DEBUG
from dmscripts.export_framework_applicant_details import export_supplier_details
from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    FRAMEWORK = arguments['<framework_slug>']
    OUTPUT_DIR = arguments['<output_dir>']

    configure_logger({"script": loglevel_DEBUG if arguments["--verbose"] else loglevel_INFO})
    logger = get_logger()

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), get_auth_token('api', STAGE))
    now = datetime.datetime.now()

    filename = FRAMEWORK + "-supplier-about-you-data-" + now.strftime("%Y-%m-%d_%H.%M-") + STAGE + ".csv"
    filepath = OUTPUT_DIR + os.sep + filename

    # Create output directory if it doesn't already exist
    if not os.path.exists(os.path.dirname(filepath)):
        try:
            os.makedirs(os.path.dirname(filepath))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    framework_lot_slugs = tuple([lot['slug'] for lot in client.get_framework(FRAMEWORK)['frameworks']['lots']])

    pool = ThreadPool(3)

    export_supplier_details(
        client, FRAMEWORK, filepath, framework_lot_slugs=framework_lot_slugs, map_impl=pool.imap, logger=logger
    )
