#!/usr/bin/env python
"""
This script requires a tab-separated file matching supplier ids to supplier names; the first column must be the
supplier ID and the second column is the supplier name, e.g.:

  12345    Supplier Name 1
  123456   Supplier Name 2
  ...

This will:
 * scan a directory for files with a filename matching <supplier_id>-document-name.<document_type>
   NOTE: all filenames in the folder and subdirectories MUST begin with a supplier ID or the script will fail

 * upload them to the S3 documents bucket for <stage> with the file path:
   <framework_slug>/<bucket_category>/<supplier_id>/<supplier_id>-document-name.<document_type>
   e.g.
   g-cloud-7/agreements/1234/1234-countersigned-framework-agreement.pdf

 * set a "download filename" that the file will be downloaded as, which is:
   <supplier-name>-<supplier-id>-<document-name>.<document-type>
   Where the <supplier-name> is determined by looking up the supplier ID from the tab-separated file

Usage:
    scripts/bulk-upload-documents.py <stage> <local_documents_directory> <framework_slug> <tsv_path> [options]

Options:
    -h --help   Show this screen.
    --file_type=<file_type>  This is the type of file [default: pdf]
    --bucket_category=<bucket_category>  This is the type  of bucket [default: agreements]
    --dry-run
"""
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
    tsv_path = arguments['<tsv_path>']
    dry_run = arguments['--dry-run']

    if dry_run:
        bucket = None
    else:
        bucket = S3(get_bucket_name(stage, bucket_category))

    supplier_name_dict = get_supplier_name_dict_from_tsv(tsv_path)
    for path in get_all_files_of_type(local_directory, file_type):
        try:
            upload_file(
                bucket, dry_run, path, framework_slug, bucket_category,
                supplier_name_dict=supplier_name_dict)
        except ValueError as e:
            print("SKIPPING: {}".format(e))
            continue
