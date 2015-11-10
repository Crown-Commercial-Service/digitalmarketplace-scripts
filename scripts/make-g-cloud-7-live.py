"""

Usage:
    scripts/make-g-cloud-7-live.py <data_api_url> <data_api_token> <draft_bucket> <documents_bucket>
"""
import sys
sys.path.insert(0, '.')

from itertools import islice
import random
import re

from docopt import docopt
from dmutils.apiclient import DataAPIClient
from dmutils.s3 import S3

DOCUMENT_KEYS = [
    'pricingDocumentURL', 'serviceDefinitionDocumentURL',
    'sfiaRateDocumentURL', 'termsAndConditionsDocumentURL',
]
FRAMEWORK_SLUG = 'g-cloud-7'


def assert_equal(one, two):
    if one != two:
        raise AssertionError("{} != {}".format(one, two))


def find_suppliers_on_framework(client, framework_slug):
    return (
        supplier for supplier in client.find_framework_suppliers(FRAMEWORK_SLUG)['supplierFrameworks']
        if supplier['onFramework']
    )


def find_submitted_draft_services(client, supplier, framework_slug):
    return (
        draft_service for draft_service in
        client.find_draft_services(supplier['supplierId'], framework=framework_slug)['services']
        if draft_service['status'] == 'submitted'
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


def make_draft_service_live(client, supplier, draft_service, framework_slug):
    print("  > Migrating draft {} - {}".format(draft_service['id'], draft_service['serviceName']))
    service_id = random.randint(1000, 10000)
    print("    > Publish draft - new service ID {}".format(service_id))
    for document_key in DOCUMENT_KEYS:
        if document_key not in draft_service:
            print("    > Skipping {}".format(document_key))
        else:
            parsed_document = parse_document_url(draft_service[document_key], framework_slug)
            assert_equal(str(parsed_document['supplier_id']), str(supplier['supplierId']))
            assert_equal(str(parsed_document['draft_id']), str(draft_service['id']))

            draft_document_path = get_draft_document_path(parsed_document, framework_slug)
            live_document_path = get_live_document_path(parsed_document, framework_slug, service_id)
            if not draft_bucket.path_exists(draft_document_path):
                raise ValueError(
                    "Draft document {} does not exist in bucket {}".format(
                        draft_document_path, draft_bucket.bucket_name))
            print("    > Copying {}:{} to {}:{}".format(
                  draft_bucket.bucket_name, draft_document_path,
                  documents_bucket.bucket_name, live_document_path))


if __name__ == '__main__':
    arguments = docopt(__doc__)

    client = DataAPIClient(arguments['<data_api_url>'], arguments['<data_api_token>'])
    draft_bucket = S3(arguments['<draft_bucket>'])
    documents_bucket = S3(arguments['<documents_bucket>'])

    suppliers = find_suppliers_on_framework(client, FRAMEWORK_SLUG)

    for supplier in islice(suppliers, 50):
        print("Migrating drafts for supplier {} - {}".format(supplier['supplierId'], supplier['supplierName']))
        draft_services = find_submitted_draft_services(client, supplier, FRAMEWORK_SLUG)

        for draft_service in draft_services:
            make_draft_service_live(client, supplier, draft_service, framework_slug)
