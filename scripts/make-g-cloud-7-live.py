"""

Usage:
    scripts/make-g-cloud-7-live.py <stage> <api_token> <draft_bucket> <documents_bucket> [--dry-run]
"""
import sys
sys.path.insert(0, '.')

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

import random
import re

from docopt import docopt
from dmscripts.env import get_api_endpoint_from_stage, get_assets_endpoint_from_stage
from dmutils.apiclient import DataAPIClient
from dmutils.s3 import S3

DOCUMENT_KEYS = [
    'pricingDocumentURL', 'serviceDefinitionDocumentURL',
    'sfiaRateDocumentURL', 'termsAndConditionsDocumentURL',
]
FRAMEWORK_SLUG = 'g-cloud-7'


def assert_equal(one, two):
    assert one == two, "{} != {}".format(one, two)


def find_suppliers_on_framework(client, framework_slug):
    return (
        supplier for supplier in client.find_framework_suppliers(FRAMEWORK_SLUG)['supplierFrameworks']
        if supplier['onFramework']
    )


def find_submitted_draft_services(client, supplier, framework_slug):
    return (
        draft_service for draft_service in
        client.find_draft_services(supplier['supplierId'], framework=framework_slug)['services']
        if draft_service['status'] == 'submitted' and not draft_service.get('serviceId')
    )


def parse_document_url(url, framework_slug):
    pattern = r'/{}/(\d+)/(\d+)-(.*)$'.format(re.escape(framework_slug))
    match = re.search(pattern, url)
    if not match:
        raise ValueError("Could not parse document URL {}".format(url))
    return {
        'supplier_id': match.group(1),
        'draft_id': match.group(2),
        'document_name': match.group(3),
    }


def get_draft_document_path(parsed_document, framework_slug):
    return '{framework_slug}/{supplier_id}/{draft_id}-{document_name}'.format(
        framework_slug=framework_slug,
        **parsed_document)


def get_live_document_path(parsed_document, framework_slug, service_id):
    return '{framework_slug}/documents/{supplier_id}/{service_id}-{document_name}'.format(
        framework_slug=framework_slug,
        service_id=service_id,
        **parsed_document)


def get_live_asset_url(live_document_path):
    return "{}/{}".format(get_assets_endpoint_from_stage(STAGE), live_document_path)


def document_copier(draft_bucket, documents_bucket, dry_run):
    def copy_document(draft_document_path, live_document_path):
        if not draft_bucket.path_exists(draft_document_path):
            raise ValueError("Draft document {} does not exist in bucket {}".format(
                draft_document_path, draft_bucket.bucket_name))
        message_suffix = "{}:{} to {}:{}".format(
            draft_bucket.bucket_name, draft_document_path,
            documents_bucket.bucket_name, live_document_path)

        if dry_run:
            print("    > not copying {}".format(message_suffix))
        else:
            documents_bucket.bucket.copy_key(live_document_path,
                                             src_bucket_name=draft_bucket.bucket_name,
                                             src_key_name=draft_document_path)
            print("    > copied {}".format(message_suffix))

    return copy_document


def make_draft_service_live(client, copy_document, draft_service, framework_slug, dry_run):
    print("  > Migrating draft {} - {}".format(draft_service['id'], draft_service['serviceName']))
    if dry_run:
        service_id = random.randint(1000, 10000)
        print("    > generating random test service ID".format(service_id))
    else:
        services = client.publish_draft_service(draft_service['id'], 'make-g-cloud-7-live script')
        service_id = services['services']['id']
        print("    > draft service published - new service ID {}".format(service_id))

    document_updates = {}
    for document_key in DOCUMENT_KEYS:
        if document_key not in draft_service:
            print("    > Skipping {}".format(document_key))
        else:
            parsed_document = parse_document_url(draft_service[document_key], framework_slug)
            assert_equal(str(parsed_document['supplier_id']), str(draft_service['supplierId']))
            assert_equal(str(parsed_document['draft_id']), str(draft_service['id']))

            draft_document_path = get_draft_document_path(parsed_document, framework_slug)
            live_document_path = get_live_document_path(parsed_document, framework_slug, service_id)

            copy_document(draft_document_path, live_document_path)
            document_updates[document_key] = get_live_asset_url(live_document_path)

    if dry_run:
        print("    > not updating document URLs {}".format(document_updates))
    else:
        client.update_service(service_id, document_updates, 'Moving documents to live bucket')
        print("    > document URLs updated")


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    api_url = get_api_endpoint_from_stage(STAGE)

    client = DataAPIClient(api_url, arguments['<api_token>'])
    DRAFT_BUCKET = S3(arguments['<draft_bucket>'])
    DOCUMENTS_BUCKET = S3(arguments['<documents_bucket>'])
    DRY_RUN = arguments['--dry-run']
    copy_document = document_copier(DRAFT_BUCKET, DOCUMENTS_BUCKET, DRY_RUN)

    suppliers = find_suppliers_on_framework(client, FRAMEWORK_SLUG)

    for supplier in suppliers:
        print("Migrating drafts for supplier {} - {}".format(supplier['supplierId'], supplier['supplierName']))
        draft_services = find_submitted_draft_services(client, supplier, FRAMEWORK_SLUG)

        for draft_service in draft_services:
            make_draft_service_live(client, copy_document, draft_service, FRAMEWORK_SLUG, DRY_RUN)
