"""Save countersigned details for framework agreements

Save countersignedAgreementPath and countersignedAgreementReturnedAt for framework agreements

For suppliers who have returned their framework agreement and had it countersigned (indicated
by a countersigned file in s3), we set their countersignedAgreementPath and
countersignedAgreementReturnedAt in the FrameworkAgreement table.

Usage:
    scripts/oneoff/save-countersigned-agreement-path.py <stage> <api_token> [--dry-run]
"""
import sys
sys.path.insert(0, '.')
import time
import getpass

from docopt import docopt
from dmapiclient import DataAPIClient
from dmscripts.env import get_api_endpoint_from_stage

from dmutils import s3
from dmutils.documents import get_agreement_document_path, COUNTERSIGNED_AGREEMENT_FILENAME


def get_countersigned_agreement_file_or_none(bucket, framework_slug, supplier_id):
    download_path = get_agreement_document_path(
        framework_slug,
        supplier_id,
        COUNTERSIGNED_AGREEMENT_FILENAME
    )
    files = bucket.list(download_path)
    return files.pop() if files else None


def get_bucket_name(stage):
    return 'digitalmarketplace-agreements-{0}-{0}'.format(stage)


if __name__ == '__main__':
    arguments = docopt(__doc__)

    data_api_url = get_api_endpoint_from_stage(arguments['<stage>'], 'api')
    client = DataAPIClient(data_api_url, arguments['<api_token>'])

    FRAMEWORKS = ['g-cloud-7', 'digital-outcomes-and-specialists']
    BUCKET_NAME = get_bucket_name(arguments['<stage>'])
    BUCKET = s3.S3(BUCKET_NAME)

    print("STARTED AT {}".format(time.strftime('%X %x %Z')))

    for framework_slug in FRAMEWORKS:
        # Get all supplier frameworks who have returned their agreement
        supplier_frameworks = client.find_framework_suppliers(
            framework_slug=framework_slug, agreement_returned=True)['supplierFrameworks']

        for supplier_framework in supplier_frameworks:
            print("======================")
            print "Supplier ID: {}, Agreement ID: {}".format(
                supplier_framework['supplierId'], supplier_framework['agreementId'])

            # Get their framework agreement
            framework_agreement = client.get_framework_agreement(supplier_framework['agreementId'])['agreement']

            # Skip if they already have a path and countersign time
            if (
                framework_agreement.get('countersignedAgreementPath') and
                framework_agreement.get('countersignedAgreementReturnedAt')
            ):
                print "PATH AND COUNTERSIGN TIME ALREADY EXISTS: {}, {}".format(
                    framework_agreement['countersignedAgreementPath'],
                    framework_agreement['countersignedAgreementReturnedAt'])
                continue

            # # Find file path from s3
            file = get_countersigned_agreement_file_or_none(
                BUCKET, framework_slug, supplier_framework['supplierId'])

            # Check file path is found
            if not file or not file.get("path"):
                print "FILE NOT FOUND FOR SUPPLIER ID: {}".format(supplier_framework['supplierId'])
                continue

            # Get meta timestamp for when file was created
            countersigned_at_time = BUCKET.bucket.get_key(
                get_agreement_document_path(
                    framework_slug,
                    supplier_framework['supplierId'],
                    COUNTERSIGNED_AGREEMENT_FILENAME
                )
            ).get_metadata('timestamp')

            # Check meta timestamp has been found
            if not countersigned_at_time:
                print "COUNTERSIGNED TIME NOT FOUND FOR SUPPLIER ID: {}".format(supplier_framework['supplierId'])
                continue

            # Save filepath and countersigned_at_time to framework agreement
            filepath = file['path']
            if arguments['--dry-run']:
                print "Dry run updating countersign path '{}' for agreement ID {}".format(
                    filepath, supplier_framework['agreementId'])
                print "Dry run updating countersign time '{}' for agreement ID {}".format(
                    countersigned_at_time, supplier_framework['agreementId'])
            else:
                print "Updating countersign path '{}' for agreement ID {}".format(
                    filepath, supplier_framework['agreementId'])
                print "Updating countersign time '{}' for agreement ID {}".format(
                    countersigned_at_time, supplier_framework['agreementId'])

                client.temp_script_countersign_agreement(
                    supplier_framework['agreementId'],
                    filepath,
                    countersigned_at_time,
                    'save-countersigned-agreement-path script run by {}'.format(getpass.getuser())
                )

    print("ENDED AT {}".format(time.strftime('%X %x %Z')))
