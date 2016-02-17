#!/usr/bin/env python
"""
This will scan a directory for files with a filename matching -<supplier_id>_Framework_Agreement.<document_type>
and upload them to the S3 documents bucket for <stage> with the file path:

<framework_slug>/<bucket_category>/<supplier_id>/<supplier_id>-<document_category>.<document_type>
e.g.
g-cloud-7/agreements/1234/1234-countersigned-framework-agreement.pdf

Usage:
    scripts/bulk-upload-documents.py <stage> <local_documents_directory> <framework_slug> <tsv_path> [options]

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
