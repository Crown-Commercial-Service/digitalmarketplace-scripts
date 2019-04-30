#!/usr/bin/env python

"""
PREREQUISITE: You'll need AWS credentials set up for the environment that you're uploading to:
              Save your aws_access_key_id and aws_secret_access_key in ~/.aws/credentials
              If you have more than one set of credentials in there then be sure to set your AWS_PROFILE environment
              variable to reference the right credentials before running the script.
              Alternatively, if this script is being run from Jenkins, do not provide any credentials and boto will use
              the Jenkins IAM role. It should have the required permissions for the bucket.

This will:
 * call the export_<suppliers|users>_for_framework endpoint from the API
 * create a CSV file from the results and save to saved to `<output-dir>/<filename>.csv` (see get-model-data.py)
 * upload the file to the S3 admin reports bucket for <stage> with the file path:
    <framework_slug>/official-details-for-suppliers-<framework_slug>.csv OR
    <framework_slug>/user-research-suppliers-on-<framework_slug>.csv OR
    <framework_slug>/all-email-accounts-for-suppliers-<framework_slug>.csv

     e.g.
     g-cloud-10/user-research-suppliers-on-g-cloud-10.csv

Usage: scripts/generate-supplier-user-csv.py <stage> <report_type> <framework_slug> [options]

Options:
    --dry-run                       Don't actually do anything
    --user-research-opted-in        Only include users who have opted in to user research
    --output-dir=<output_dir>       Location to store CSV file [default: data]

"""
import os
import sys
sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.generate_supplier_user_csv import generate_csv_and_upload_to_s3
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging
from dmscripts.helpers.s3_helpers import get_bucket_name
from dmutils.env_helpers import get_api_endpoint_from_stage

from docopt import docopt
from dmapiclient import DataAPIClient

from dmutils.s3 import S3


logger = logging_helpers.configure_logger({
    'dmapiclient.base': logging.WARNING,
})


if __name__ == '__main__':
    arguments = docopt(__doc__)

    stage = arguments['<stage>']
    data_api_client = DataAPIClient(get_api_endpoint_from_stage(stage), get_auth_token('api', stage))
    report_type = arguments['<report_type>']
    framework_slug = arguments['<framework_slug>']
    output_dir = arguments['--output-dir']
    user_research_opted_in = arguments['--user-research-opted-in'] or None
    dry_run = arguments['--dry-run']

    if report_type not in ['users', 'suppliers']:
        logger.error('Please specify users or suppliers to be exported.')
        sys.exit(1)

    if not os.path.exists(output_dir):
        logger.info("Creating {} directory".format(output_dir))
        os.makedirs(output_dir)

    if dry_run:
        bucket = None
    else:
        if stage == 'local':
            bucket = S3('digitalmarketplace-dev-uploads')
        else:
            # e.g. preview would give 'digitalmarketplace-reports-preview-preview'
            bucket = S3(get_bucket_name(stage, "reports"))

    ok = generate_csv_and_upload_to_s3(
        bucket,
        framework_slug,
        report_type,
        output_dir,
        data_api_client,
        dry_run=dry_run,
        user_research_opted_in=user_research_opted_in,
        logger=logger,
    )

    if not ok:
        sys.exit(1)
