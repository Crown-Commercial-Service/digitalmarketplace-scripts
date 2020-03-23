#!/usr/bin/env python3
"""Generate DOS opportunity data export CSV

Loads data from the Brief and BriefResponse API models, filters for closed/awarded briefs and stores the output
in the CSV.

Usage:
    scripts/export-dos-opportunities.py [options] <stage>

Options:
    -h --help       Show this screen.
    -v --verbose    Print apiclient INFO messages.
    --dry-run       Generate the file but do not upload to S3
    --output-dir=<output_dir>  Directory to write csv files to [default: data]
"""
import os
import sys
sys.path.insert(0, '.')

from docopt import docopt

from dmapiclient import DataAPIClient

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.logging_helpers import logging, configure_logger
from dmscripts.export_dos_opportunities import (
    get_latest_dos_framework, get_brief_data, write_rows_to_csv, upload_file_to_s3
)
from dmutils.env_helpers import get_api_endpoint_from_stage
from dmutils.s3 import S3


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    OUTPUT_DIR = arguments['--output-dir']
    DRY_RUN = arguments['--dry-run']

    logging_config = {'dmapiclient': logging.INFO} if bool(arguments.get('--verbose')) \
        else {'dmapiclient': logging.WARNING}
    logger = configure_logger(logging_config)

    # TODO: use pathlib
    if not os.path.exists(OUTPUT_DIR):
        logger.info("Creating {} directory".format(OUTPUT_DIR))
        os.makedirs(OUTPUT_DIR)

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), get_auth_token('api', STAGE))

    latest_framework_slug = get_latest_dos_framework(client)

    DOWNLOAD_FILE_NAME = 'opportunity-data.csv'
    file_path = os.path.join(OUTPUT_DIR, DOWNLOAD_FILE_NAME)
    bucket_name = 'digitalmarketplace-communications-{}-{}'.format(STAGE, STAGE)
    key_name = '{}/communications/data/{}'.format(latest_framework_slug, DOWNLOAD_FILE_NAME)

    logger.info('Exporting DOS opportunity data to CSV')

    # Get the data
    rows = get_brief_data(client, logger)

    # Construct CSV
    write_rows_to_csv(rows, file_path, logger)

    # Grab bucket
    bucket = S3(bucket_name)

    # Upload to S3
    upload_file_to_s3(
        file_path,
        bucket,
        key_name,
        DOWNLOAD_FILE_NAME,
        dry_run=DRY_RUN,
        logger=logger
    )
