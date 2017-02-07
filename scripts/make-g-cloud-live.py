"""

For a G-Cloud style framework (with uploaded documents to migrate) this will:
 1. Find all suppliers awarded onto the framework
 2. Find all their submitted draft services on the framework
 3. Migrate these from drafts to "real" services, which includes moving documents to the live documents bucket
    and updating document URLs in the migrated version of the services
Usage:
    scripts/make-g-cloud-live.py <framework_slug> <stage> <api_token> <draft_bucket> <documents_bucket> [--dry-run]
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
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage, get_assets_endpoint_from_stage
from dmscripts.helpers.framework_helpers import find_suppliers_on_framework, get_submitted_drafts
from dmapiclient import DataAPIClient
from dmutils.s3 import S3

DOCUMENT_KEYS = [
    'pricingDocumentURL', 'serviceDefinitionDocumentURL',
    'sfiaRateDocumentURL', 'termsAndConditionsDocumentURL',
]


def assert_equal(one, two):
    assert one == two, u"{} != {}".format(one, two)


def parse_document_url(url, framework_slug):
    pattern = r'/{}/submissions/(\d+)/(\d+)-(.*)$'.format(re.escape(framework_slug))
    match = re.search(pattern, url)
    if not match:
        raise ValueError(u"Could not parse document URL {}".format(url))
    return {
        'supplier_id': match.group(1),
        'draft_id': match.group(2),
        'document_name': match.group(3),
    }


def get_draft_document_path(parsed_document, framework_slug):
    return u'{framework_slug}/submissions/{supplier_id}/{draft_id}-{document_name}'.format(
        framework_slug=framework_slug,
        **parsed_document)


def get_live_document_path(parsed_document, framework_slug, service_id):
    return u'{framework_slug}/documents/{supplier_id}/{service_id}-{document_name}'.format(
        framework_slug=framework_slug,
        service_id=service_id,
        **parsed_document)


def get_live_asset_url(live_document_path):
    return u"{}/{}".format(get_assets_endpoint_from_stage(STAGE), live_document_path)


def document_copier(draft_bucket, documents_bucket, dry_run):
    def copy_document(draft_document_path, live_document_path):
        if not draft_bucket.path_exists(draft_document_path):
            raise ValueError(u"Draft document {} does not exist in bucket {}".format(
                draft_document_path, draft_bucket.bucket_name))
        message_suffix = u"{}:{} to {}:{}".format(
            draft_bucket.bucket_name, draft_document_path,
            documents_bucket.bucket_name, live_document_path)

        if dry_run:
            print(u"    > not copying {}".format(message_suffix))
        else:
            key = documents_bucket.bucket.copy_key(live_document_path,
                                                   src_bucket_name=draft_bucket.bucket_name,
                                                   src_key_name=draft_document_path)
            key.set_acl('public-read')
            print(u"    > copied {}".format(message_suffix))

    return copy_document


def make_draft_service_live(client, copy_document, draft_service, framework_slug, dry_run):
    try:
        print(u"  > Migrating draft {} - {}".format(draft_service['id'], draft_service['serviceName']))
        if dry_run:
            service_id = random.randint(1000, 10000)
            print(u"    > generating random test service ID: {}".format(service_id))
        else:
            services = client.publish_draft_service(draft_service['id'], 'make-g-cloud-live script')
            service_id = services['services']['id']
            print(u"    > draft service published - new service ID {}".format(service_id))

        document_updates = {}
        for document_key in DOCUMENT_KEYS:
            if document_key not in draft_service:
                print(u"    > Skipping {}".format(document_key))
            else:
                parsed_document = parse_document_url(draft_service[document_key], framework_slug)
                assert_equal(str(parsed_document['supplier_id']), str(draft_service['supplierId']))
                assert_equal(str(parsed_document['draft_id']), str(draft_service['id']))

                draft_document_path = get_draft_document_path(parsed_document, framework_slug)
                live_document_path = get_live_document_path(parsed_document, framework_slug, service_id)

                copy_document(draft_document_path, live_document_path)
                document_updates[document_key] = get_live_asset_url(live_document_path)

        if dry_run:
            print(u"    > not updating document URLs {}".format(document_updates))
        else:
            client.update_service(service_id, document_updates, 'Moving documents to live bucket')
            print("    > document URLs updated")
    except Exception as e:
        print("ERROR MAKING DRAFT '{}' LIVE: {}".format(draft_service['id'], e.message))


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    api_url = get_api_endpoint_from_stage(STAGE)

    client = DataAPIClient(api_url, arguments['<api_token>'])
    DRAFT_BUCKET = S3(arguments['<draft_bucket>'])
    DOCUMENTS_BUCKET = S3(arguments['<documents_bucket>'])
    DRY_RUN = arguments['--dry-run']
    FRAMEWORK_SLUG = arguments['<framework_slug>']
    copy_document = document_copier(DRAFT_BUCKET, DOCUMENTS_BUCKET, DRY_RUN)

    suppliers = find_suppliers_on_framework(client, FRAMEWORK_SLUG)

    for supplier in suppliers:
        print(u"Migrating drafts for supplier {} - {}".format(supplier['supplierId'], supplier['supplierName']))
        draft_services = get_submitted_drafts(client, FRAMEWORK_SLUG, supplier['supplierId'])

        for draft_service in draft_services:
            make_draft_service_live(client, copy_document, draft_service, FRAMEWORK_SLUG, DRY_RUN)
