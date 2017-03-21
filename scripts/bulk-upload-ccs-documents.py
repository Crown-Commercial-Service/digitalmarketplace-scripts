"""
!!! NOTE: THIS IS AN OLD SCRIPT AND PROBABLY NOT THE ONE YOU WANT !!!

PREREQUISITE: You'll need AWS credentials set up for the environment that you're uploading to:
              Save your aws_access_key_id and aws_secret_access_key in ~/.aws/credentials
              If you have more than one set of credentials in there then be sure to set your AWS_PROFILE environment
              variable to reference the right credentials before running the script.

For uploading result letters and framework agreements you should prefer bulk-upload-documents.py because it sets a
nice supplier-friendly filename at the same time.

This will:
 * scan a directory for files with filenames matching ignored-stuff-<supplier_id>-ignored-stuff.<document_type>

 * upload them to the S3 documents bucket for <stage> with the file path:
   <framework_slug>/<bucket_category>/<supplier_id>/<supplier_id>-<document_category>.<document_type>
   e.g.
   g-cloud-7/agreements/1234/1234-countersigned-framework-agreement.pdf

Usage:
scripts/bulk-upload-ccs-documents.py <stage> <local_documents_directory> <framework_slug> <document_category> [options]

Options:
    --bucket_category=<bucket_category>  [default: agreements]
    --document_type=<document_type>     [default: pdf]
    --dry-run
"""
import sys
sys.path.insert(0, '.')

from dmscripts.bulk_upload_documents import get_bucket_name, get_all_files_of_type, upload_file

from docopt import docopt

from dmutils.s3 import S3


if __name__ == '__main__':
    arguments = docopt(__doc__)

    stage = arguments['<stage>']
    framework_slug = arguments['<framework_slug>']
    local_directory = arguments['<local_documents_directory>']
    bucket_category = arguments['--bucket_category']
    document_category = arguments['<document_category>']
    document_type = arguments['--document_type']
    dry_run = arguments['--dry-run']

    document_categories = ['result-letter', 'framework-agreement']

    if document_category not in document_categories:
        print('Document needs to be one of {}'.format(document_categories))
        if document_category in ('signed-framework-agreement', 'countersigned-framework-agreement'):
            print('Signed and countersigned agreement paths now need to be stored in database so cannot be uploaded '
                  'using this script.')
        sys.exit(1)

    if dry_run:
        bucket = None
    else:
        bucket = S3(get_bucket_name(stage, bucket_category))

    for path in get_all_files_of_type(local_directory, document_type):
        try:
            upload_file(bucket, dry_run, path, framework_slug, bucket_category,
                        document_category, document_type)
        except ValueError as e:
            print("SKIPPING: {}".format(e))
            continue
