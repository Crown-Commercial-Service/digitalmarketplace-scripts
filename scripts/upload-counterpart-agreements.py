"""
This will:
 * scan a directory for pdf files (they should be in the format <supplier_id>-some-ignored-words.pdf but this isn't
   enforced)
   and for each file:

   * get the SupplierFramework object for the supplier

   * upload them to the S3 documents bucket for <stage> with the file path:
     <framework_slug>/agreements/<supplier_id>/<supplier_id>-counterpart-signature-page.pdf
     e.g.
     g-cloud-8/agreements/1234/1234-counterpart-signature-page.pdf

   * set a "download filename" that the file will be downloaded as, which is:
     <supplier-name>-<supplier-id>-<document-name>.<document-type>
     where supplier_name is the sanitised version of the name from their supplier declaration for the framework

   * set the "countersigned agreement path" in the current FrameworkAgreement referenced by the SupplierFramework

Usage:
   scripts/upload-counterpart-agreemets.py <stage> <api_token> <documents_directory> <framework_slug> [--dry-run]

"""

import sys
sys.path.insert(0, '.')

from dmscripts.env import get_api_endpoint_from_stage
from dmscripts.bulk_upload_documents import get_bucket_name, get_all_files_of_type
from dmscripts.upload_counterpart_agreements import upload_counterpart_file
from docopt import docopt
from dmapiclient import DataAPIClient

from dmutils.s3 import S3


if __name__ == '__main__':
    arguments = docopt(__doc__)

    stage = arguments['<stage>']
    client = DataAPIClient(get_api_endpoint_from_stage(stage), arguments['<api_token>'])
    framework_slug = arguments['<framework_slug>']
    document_directory = arguments['<documents_directory>']
    dry_run = arguments['--dry-run']

    if dry_run:
        bucket = None
    else:
        bucket = S3(get_bucket_name(stage, "agreements"))

    for file_path in get_all_files_of_type(document_directory, "pdf"):
        upload_counterpart_file(bucket, framework_slug, file_path, dry_run, client)
