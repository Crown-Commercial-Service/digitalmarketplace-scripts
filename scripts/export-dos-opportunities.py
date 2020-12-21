#!/usr/bin/env python3
"""Generate DOS opportunity data export CSV

Loads data from the Brief and BriefResponse API models, filters for
closed/awarded briefs and stores the output in the CSV.

This script generates two CSVs, one with buyer user details and one without.

The CSV without buyer user details is made publically available by uploading to
the communications bucket, the CSV with buyer user details should be available
to admins only so it is uploaded to the reports bucket.

Usage:
    scripts/export-dos-opportunities.py [options] <stage>

Options:
    -h --help       Show this screen.
    -v --verbose    Print apiclient INFO messages.
    --dry-run       Generate the file but do not upload to S3
    --output-dir=<output_dir>  Directory to write csv files to [default: data]
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt

from dmapiclient import DataAPIClient

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.logging_helpers import logging, configure_logger
from dmscripts.export_dos_opportunities import export_dos_opportunities
from dmutils.env_helpers import get_api_endpoint_from_stage


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    OUTPUT_DIR = arguments['--output-dir']
    DRY_RUN = arguments['--dry-run']

    logging_config = {
        'dmapiclient': logging.INFO} if bool(arguments.get('--verbose')) \
        else {'dmapiclient': logging.WARNING}
    logger = configure_logger(logging_config)

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), get_auth_token('api', STAGE))

    export_dos_opportunities(client, logger, STAGE, OUTPUT_DIR, DRY_RUN)
