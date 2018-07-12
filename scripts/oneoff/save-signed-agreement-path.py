"""Save signedAgreementPath for framework agreement

For suppliers who have returned their framework agreement, if there is no
signedAgreementPath set in the FrameworkAgreement table then check s3 for their
most recently uploaded signed framework agreement file and update the
FrameworkAgreement record with this file path.

Usage:
    scripts/oneoff/save-signed-agreement-path.py <stage> [--dry-run]
"""
import sys
sys.path.insert(0, '.')
import time
import getpass

from docopt import docopt
from dmapiclient import DataAPIClient
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage

from dmutils import s3
from dmutils.documents import get_agreement_document_path, SIGNED_AGREEMENT_PREFIX


def get_most_recently_uploaded_agreement_file_or_none(bucket, framework_slug, supplier_id):
    download_path = get_agreement_document_path(
        framework_slug,
        supplier_id,
        SIGNED_AGREEMENT_PREFIX
    )
    files = bucket.list(download_path)
    return files.pop() if files else None


def get_bucket_name(stage):
    return 'digitalmarketplace-agreements-{0}-{0}'.format(stage)


if __name__ == '__main__':
    arguments = docopt(__doc__)

    data_api_url = get_api_endpoint_from_stage(arguments['<stage>'], 'api')
    client = DataAPIClient(data_api_url, get_auth_token('api', arguments['<stage>']))

    FRAMEWORKS = ['g-cloud-7', 'g-cloud-8', 'digital-outcomes-and-specialists']
    BUCKET_NAME = get_bucket_name(arguments['<stage>'])
    BUCKET = s3.S3(BUCKET_NAME)
    print("STARTED AT {}".format(time.strftime('%X %x %Z')))
    for framework_slug in FRAMEWORKS:
        # Get all supplier frameworks who have returned their agreement
        supplier_frameworks = client.find_framework_suppliers(
            framework_slug=framework_slug, agreement_returned=True)['supplierFrameworks']

        for supplier_framework in supplier_frameworks:
            print("======================")
            print("Supplier ID: {}, Agreement ID: {}".format(
                supplier_framework['supplierId'], supplier_framework['agreementId']))

            # Get their framework agreement
            framework_agreement = client.get_framework_agreement(supplier_framework['agreementId'])['agreement']

            # Skip if they already have a path
            if framework_agreement.get('signedAgreementPath'):
                print("PATH ALREADY EXISTS: {}".format(framework_agreement['signedAgreementPath']))
                continue

            # Find file path from s3
            file = get_most_recently_uploaded_agreement_file_or_none(
                BUCKET, framework_slug, supplier_framework['supplierId'])

            # Check file path is found
            if not file or not file.get("path"):
                print("FILE NOT FOUND FOR SUPPLIER ID: {}".format(supplier_framework['supplierId']))
                continue
            else:
                print("S3 FILEPATH: {}".format(file["path"]))

            # Save filepath to framework agreement
            if arguments['--dry-run']:
                print("Would update {} filepath to agreement ID {}".format(
                    file["path"], supplier_framework['agreementId']))
            else:
                print("Updating {} filepath to agreement ID {}".format(
                    file["path"], supplier_framework['agreementId']))
                client.update_framework_agreement(
                    supplier_framework['agreementId'],
                    {"signedAgreementPath": file["path"]},
                    'save-signed-agreement-path script run by {}'.format(getpass.getuser())
                )
    print("ENDED AT {}".format(time.strftime('%X %x %Z')))
