#!/usr/bin/env python
"""

Usage:
    scripts/check-g-cloud-7-live.py <stage> <api_token> <draft_bucket> <documents_bucket>
"""
import sys
sys.path.insert(0, '.')

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

import itertools
import functools
from multiprocessing.pool import ThreadPool
from docopt import docopt
from dmscripts.env import get_api_endpoint_from_stage, get_assets_endpoint_from_stage
from dmscripts.logging import configure_logger
from dmutils.apiclient import DataAPIClient
from dmutils.s3 import S3
import requests

DOCUMENT_KEYS = [
    'pricingDocumentURL', 'serviceDefinitionDocumentURL',
    'sfiaRateDocumentURL', 'termsAndConditionsDocumentURL',
]
FRAMEWORK_SLUG = 'g-cloud-7'
logger = configure_logger()


def find_suppliers_on_framework(client, framework_slug):
    return (
        supplier
        for supplier
        in client.find_framework_suppliers(framework_slug)['supplierFrameworks']
        if supplier['onFramework']
    )


def find_drafts_for_supplier(client, supplier_id, framework_slug):
    return (
        draft_service
        for draft_service
        in client.find_draft_services(supplier_id, framework=framework_slug)['services']
        if draft_service['status'] == 'submitted'
    )


def find_drafts(client, framework_slug):
    return itertools.chain.from_iterable(
        find_drafts_for_supplier(client, supplier['supplierId'], framework_slug)
        for supplier
        in find_suppliers_on_framework(client, framework_slug)
    )


def check_draft_and_service(client, draft):
    try:
        check_draft(draft)
        service = client.get_service(draft['serviceId'])['services']
        check_document_urls(service)
    except AssertionError as e:
        logger.error(e)


def check_draft(draft):
    assert isinstance(draft['serviceId'], str)
    assert draft['serviceId'].isdigit()


def check_document_urls(service):
    domain = "assets.digitalmarketplace.service.gov.uk"
    for key in DOCUMENT_KEYS:
        if key in service:
            url = urlparse.urlparse(service[key])
            assert url.netloc == domain, "Domain error: {} {}".format(service['id'], service[key])
            assert url.path.startswith("/g-cloud-7/documents")
            response = requests.head(service[key])
            assert response.status_code == 200


def check_migration(client, stage, framework_slug, draft_bucket, documents_bucket):
    do_check_draft_and_service = functools.partial(check_draft_and_service, client)
    pool = ThreadPool(10)
    drafts = pool.imap_unordered(
        do_check_draft_and_service,
        find_drafts(client, framework_slug))
    for draft in drafts:
        pass


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    api_url = get_api_endpoint_from_stage(STAGE)

    client = DataAPIClient(api_url, arguments['<api_token>'])
    DRAFT_BUCKET = S3(arguments['<draft_bucket>'])
    DOCUMENTS_BUCKET = S3(arguments['<documents_bucket>'])

    check_migration(client, STAGE, FRAMEWORK_SLUG, DRAFT_BUCKET, DOCUMENTS_BUCKET)
