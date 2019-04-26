#!/usr/bin/env python
"""
!!! NOTE: This script is the preferred way to upload framework agreement signature pages and "fail" letters.
!!! You can't upload countersigned/counterpart pages with this script because the DB also needs to be updated for those.

PREREQUISITE: You'll need AWS credentials set up for the environment that you're uploading to:
              Save your aws_access_key_id and aws_secret_access_key in ~/.aws/credentials
              If you have more than one set of credentials in there then be sure to set your AWS_PROFILE environment
              variable to reference the right credentials before running the script.


This script requires a tab-separated file matching supplier ids to supplier names; the first column must be the
supplier ID and the second column is the supplier name, e.g.:

  12345    Supplier Name 1
  123456   Supplier Name 2
  ...

This will:
 * scan a directory for files with a filename matching <supplier_id>-document-name.<file_type>
   NOTE: all filenames in the folder and subdirectories MUST begin with a supplier ID or the script will fail

 * upload them to the S3 documents bucket for <stage> with the file path:
   <framework_slug>/<bucket_category>/<supplier_id>/<supplier_id>-document-name.<file_type>
   e.g.
   digital-outcomes-and-specialists-2/agreements/1234/1234-signature-page.pdf

 * Optionally set a "download filename" that the file will be downloaded as, which is:
   <supplier_name>-<supplier_id>-document-name.<file_type>
   Where the <supplier_name> is determined by looking up the supplier ID from the tab-separated file

Usage:
    scripts/bulk-upload-documents.py <stage> <local_documents_directory> <framework_slug> [options]

Options:
    -h --help   Show this screen.
    --tsv-path=<tsv_path>                TSV of supplier IDs and names
    --file_type=<file_type>              This is the type of file [default: pdf]
    --bucket_category=<bucket_category>  This is the type  of bucket [default: agreements]
    --dry-run
"""
import os
import sys
sys.path.insert(0, '.')

from dmscripts.bulk_upload_documents import get_bucket_name, get_all_files_of_type, \
    upload_file, get_supplier_name_dict_from_tsv

from docopt import docopt

from dmutils.s3 import S3


if __name__ == '__main__':
    arguments = docopt(__doc__)

    stage = arguments['<stage>']
    framework_slug = arguments['<framework_slug>']
    local_directory = arguments['<local_documents_directory>']
    bucket_category = arguments['--bucket_category']
    file_type = arguments['--file_type']
    tsv_path = arguments['--tsv-path']
    dry_run = arguments['--dry-run']

    if dry_run:
        bucket = None
    else:
        bucket = S3(get_bucket_name(stage, bucket_category))

    supplier_name_dict = get_supplier_name_dict_from_tsv(tsv_path)

    if not os.path.exists(local_directory):
        print(f"Local directory {local_directory} not found. Aborting upload.")
        exit(1)

    for path in get_all_files_of_type(local_directory, file_type):
        try:
            upload_file(
                bucket, dry_run, path, framework_slug, bucket_category,
                supplier_name_dict=supplier_name_dict
            )
        except ValueError as e:
            print("SKIPPING: {}".format(e))
            continue
