#!/usr/bin/env python3
"""
PREREQUISITE: For document migration to work you'll need AWS credentials set up for the relevant environment:
              Save your aws_access_key_id and aws_secret_access_key in ~/.aws/credentials
              If you have more than one set of credentials in there then be sure to set your AWS_PROFILE environment
              variable to reference the right credentials before running the script.
              Alternatively, if this script is being run from Jenkins, do not provide any credentials and boto will use
              the Jenkins IAM role. It should have the required permissions for the buckets.

For a G-Cloud style framework (with uploaded documents to migrate) this will:
 1. Find all suppliers awarded onto the framework
 2. Find all their submitted draft services on the framework
 3. Migrate these from drafts to "real" services, which includes moving documents to the live documents bucket
    and updating document URLs in the migrated version of the services
Usage:
    scripts/publish-g-cloud-draft-services.py <framework_slug> <stage> <api_token> <draft_bucket>
        <documents_bucket> [--dry-run] [--draft-ids=<filename>]

If you specify the `--draft-ids` parameter, pass in list of newline-separated draft ids. This script will then do a
full re-publish of just those drafts (i.e. try to re-publish it, and then copy the documents across again and update
those links).
"""
import backoff
import collections
from datetime import datetime
from docopt import docopt
import random
import re
import sys

sys.path.insert(0, '.')  # noqa

import dmapiclient
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage, get_assets_endpoint_from_stage
from dmscripts.helpers.framework_helpers import find_suppliers_on_framework, get_submitted_drafts
from dmapiclient import DataAPIClient
from dmutils.s3 import S3, S3ResponseError

DOCUMENT_KEYS = [
    'pricingDocumentURL', 'serviceDefinitionDocumentURL',
    'sfiaRateDocumentURL', 'termsAndConditionsDocumentURL',
]


def assert_equal(one, two):
    assert one == two, "{} != {}".format(one, two)


def parse_document_url(url, framework_slug):
    pattern = r'/{}/submissions/(\d+)/(\d+)-(.*)$'.format(re.escape(framework_slug))
    match = re.search(pattern, url)
    if not match:
        raise ValueError("Could not parse document URL {}".format(url))
    return {
        'supplier_id': match.group(1),
        'draft_id': match.group(2),
        'document_name': match.group(3),
    }


def get_draft_document_path(parsed_document, framework_slug):
    return '{framework_slug}/submissions/{supplier_id}/{draft_id}-{document_name}'.format(
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
            print("    > dry run: skipped copying {}".format(message_suffix))
        else:
            documents_bucket.copy(src_bucket=draft_bucket.bucket_name, src_key=draft_document_path,
                                  target_key=live_document_path)
            print("    > copied {}".format(message_suffix))

    return copy_document


@backoff.on_exception(backoff.expo, S3ResponseError, max_tries=5)
def copy_draft_documents(client, copy_document, draft_service, framework_slug, dry_run, service_id):
    document_updates = {}
    for document_key in DOCUMENT_KEYS:
        if document_key in draft_service:
            parsed_document = parse_document_url(draft_service[document_key], framework_slug)
            assert_equal(str(parsed_document['supplier_id']), str(draft_service['supplierId']))
            assert_equal(str(parsed_document['draft_id']), str(draft_service['id']))

            draft_document_path = get_draft_document_path(parsed_document, framework_slug)
            live_document_path = get_live_document_path(parsed_document, framework_slug, service_id)

            try:
                copy_document(draft_document_path, live_document_path)

            except S3ResponseError as e:
                if str(e) != 'Target key already exists in S3':
                    raise e

            document_updates[document_key] = get_live_asset_url(live_document_path)

    if dry_run:
        print("    > dry run: skipped updating document URLs {}".format(document_updates))
    else:
        client.update_service(service_id, document_updates, 'Moving documents to live bucket')
        print("    > document URLs updated")


@backoff.on_exception(backoff.expo, dmapiclient.HTTPError, max_tries=5)
def make_draft_service_live(client, copy_document, draft_service, framework_slug, dry_run,
                            continue_if_published=False):
    print("  > Migrating draft {}".format(draft_service['id']))
    if dry_run:
        service_id = random.randint(1000, 10000)
        print("    > dry run: generating random test service ID: {}".format(service_id))
    else:
        try:
            services = client.publish_draft_service(draft_service['id'], 'publish g-cloud draft services script')
            service_id = services['services']['id']
            print("    > draft service published - new service ID {}".format(service_id))

        except dmapiclient.HTTPError as e:
            if continue_if_published and e.status_code == 400 \
                    and str(e).startswith('Cannot re-publish a submitted service'):
                published_draft = client.get_draft_service(draft_service['id'])
                services = client.get_service(published_draft['services']['serviceId'])
                service_id = services['services']['id']
            else:
                raise e

    copy_draft_documents(client, copy_document, draft_service, framework_slug, dry_run, service_id)


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    api_url = get_api_endpoint_from_stage(STAGE)

    client = DataAPIClient(api_url, arguments['<api_token>'])
    DRAFT_BUCKET = S3(arguments['<draft_bucket>'])
    DOCUMENTS_BUCKET = S3(arguments['<documents_bucket>'])
    DRY_RUN = arguments['--dry-run']
    FRAMEWORK_SLUG = arguments['<framework_slug>']
    DRAFT_IDS = arguments['--draft-ids']

    copy_document = document_copier(DRAFT_BUCKET, DOCUMENTS_BUCKET, DRY_RUN)

    results = collections.Counter({'success': 0, 'fail': 0})

    def get_draft_services():
        if DRAFT_IDS:
            with open(DRAFT_IDS) as draft_ids:
                draft_ids = [line.strip() for line in draft_ids.read().split()]

            for draft_id in draft_ids:
                yield client.get_draft_service(draft_id)['services']

        else:
            suppliers = find_suppliers_on_framework(client, FRAMEWORK_SLUG)
            for supplier in suppliers:
                print("Migrating drafts for supplier {}".format(supplier['supplierId']))
                for draft in get_submitted_drafts(client, FRAMEWORK_SLUG, supplier['supplierId']):
                    yield draft

    for draft_service in get_draft_services():
        try:
            make_draft_service_live(client, copy_document, draft_service, FRAMEWORK_SLUG, DRY_RUN,
                                    continue_if_published=True if DRAFT_IDS else False)
            results.update({'success': 1})
        except Exception as e:
            print("{} ERROR MIGRATING DRAFT {} TO LIVE: {}".format(datetime.now(), draft_service['id'], e))
            results.update({'fail': 1})

    print("Successfully published {} G-Cloud services".format(results.get('success')))
    if results.get('fail'):
        print("Failed to publish {} services because of errors".format(results.get('fail')))
    exit(results.get('fail'))
