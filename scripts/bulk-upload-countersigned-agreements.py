"""
This will scan a directory for files with a filename matching -<supplier_id>_Framework_Agreement
and upload them to the S3 agreements bucket for <stage> with the file path
g-cloud-7/agreements/<supplier_id>/<supplier_id>-countersigned-framework-agreement.pdf

Usage:
    scripts/bulk-upload-countersigned-agreements.py <local_directory> <stage> [--dry-run]
"""
import sys
from dmutils.documents import get_countersigned_agreement_document_path
import re

sys.path.insert(0, '.')

import os

from docopt import docopt

from dmutils.s3 import S3
from dmscripts.env import get_api_endpoint_from_stage


def get_all_pdfs(local_directory):
    for root, subfolder, files in os.walk(local_directory):
        for filename in files:
            if filename.endswith('.pdf'):
                yield os.path.join(root, filename)


def upload_agreement(bucket, dry_run, file_path):
    supplier_id = get_supplier_id_from_framework_file_path(path)
    upload_path = get_countersigned_agreement_document_path("g-cloud-7", supplier_id)
    print("UPLOADING: '{}' to '{}'".format(file_path, upload_path))
    if not dry_run:
        with open(file_path) as file_contents:
            bucket.save(upload_path, file_contents, acl='public-read', move_prefix=None)


def get_bucket_name(stage):
    bucket_name = 'digitalmarketplace-agreements-{0}-{0}'.format(stage)
    print("BUCKET: {}".format(bucket_name))
    return bucket_name


def get_supplier_id_from_framework_file_path(path):
    # We have been told by CCS that filenames will be exactly the same as the unsigned agreement files
    # e.g. Sanitised_Supplier_Name-123456_Framework_Agreement.pdf
    match = re.search(r'-(\d{5,6})_Framework_Agreement', path)
    if not match:
        raise ValueError("Could not find supplier ID in path {}".format(path))
    return match.group(1)


if __name__ == '__main__':
    arguments = docopt(__doc__)

    stage = arguments['<stage>']
    local_directory = arguments['<local_directory>']
    dry_run = arguments['--dry-run']

    api_url = get_api_endpoint_from_stage(stage)

    if dry_run:
        bucket = None
    else:
        bucket = S3(get_bucket_name(stage))

    for path in get_all_pdfs(local_directory):
        try:
            upload_agreement(bucket, dry_run, path)
        except ValueError as e:
            print("SKIPPING: {}".format(e))
            continue
