import random
import re
from urllib.parse import urljoin

import backoff

import dmapiclient
from dmscripts.helpers.framework_helpers import find_suppliers_on_framework
from dmscripts.helpers.logging_helpers import get_logger
from dmutils.s3 import S3ResponseError


def _parse_document_url(url, framework_slug):
    pattern = r'/{}/submissions/(\d+)/(\d+)-(.*)$'.format(re.escape(framework_slug))
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Could not parse document URL {url!r}")
    return {
        'supplier_id': match.group(1),
        'draft_id': match.group(2),
        'document_name': match.group(3),
    }


def _get_draft_document_path(parsed_document_url, framework_slug):
    return '{framework_slug}/submissions/{supplier_id}/{draft_id}-{document_name}'.format(
        framework_slug=framework_slug,
        **parsed_document_url)


def _get_live_document_path(parsed_document_url, framework_slug, service_id):
    return '{framework_slug}/documents/{supplier_id}/{service_id}-{document_name}'.format(
        framework_slug=framework_slug,
        service_id=service_id,
        **parsed_document_url)


def _copy_document(draft_bucket, documents_bucket, draft_document_path, live_document_path, dry_run):
    if not draft_bucket.path_exists(draft_document_path):
        raise ValueError(f"Draft document {draft_document_path} does not exist in bucket {draft_bucket.bucket_name}")

    message_suffix = f"{draft_bucket.bucket_name}:{draft_document_path} to " \
        f"{documents_bucket.bucket_name}:{live_document_path}"

    if dry_run:
        get_logger().info("dry run: skipped copying %s", message_suffix)
    else:
        get_logger().info("copying %s", message_suffix)
        documents_bucket.copy(
            src_bucket=draft_bucket.bucket_name,
            src_key=draft_document_path,
            target_key=live_document_path,
            acl='public-read',
        )


@backoff.on_exception(backoff.expo, S3ResponseError, max_tries=5)
def copy_draft_documents(
    draft_bucket,
    documents_bucket,
    document_keys,
    live_assets_endpoint,
    client,
    framework_slug,
    draft_service,
    service_id,
    dry_run=True,
):
    if not document_keys:
        return

    document_updates = {}
    for document_key in document_keys:
        if document_key in draft_service:
            parsed_document_url = _parse_document_url(draft_service[document_key], framework_slug)

            if str(parsed_document_url['supplier_id']) != str(draft_service['supplierId']):
                raise ValueError(
                    f"supplier id mismatch: {str(parsed_document_url['supplier_id'])!r} != "
                    f"{str(draft_service['supplierId'])!r}"
                )
            if str(parsed_document_url['draft_id']) != str(draft_service['id']):
                raise ValueError(
                    f"draft id mismatch: {str(parsed_document_url['draft_id'])!r} != "
                    f"{str(draft_service['id'])!r}"
                )

            draft_document_path = _get_draft_document_path(parsed_document_url, framework_slug)
            live_document_path = _get_live_document_path(parsed_document_url, framework_slug, service_id)

            try:
                _copy_document(draft_bucket, documents_bucket, draft_document_path, live_document_path, dry_run)

            except ValueError as e:
                if not str(e).startswith('Target key already exists in S3'):
                    raise e

            document_updates[document_key] = urljoin(live_assets_endpoint, live_document_path)

    if dry_run:
        get_logger().info(
            "supplier %s: draft %s: dry run: skipped updating document URLs: %s",
            draft_service["supplierId"],
            draft_service['id'],
            str(document_updates).replace("{", "{{").replace("}", "}}"),
        )
    else:
        client.update_service(service_id, document_updates, user='publish_draft_services.py')


def publish_draft_service(
    client,
    draft_service,
    dry_run=True,
):
    get_logger().info("supplier %s: draft %s: publishing", draft_service["supplierId"], draft_service['id'])
    previously_published = False

    if draft_service.get("serviceId"):
        # This draft service already has a service id, it has already been published.
        service_id = draft_service["serviceId"]
        get_logger().warning(
            "supplier %s: draft %s: skipped publishing - already has service id: %s",
            draft_service["supplierId"],
            draft_service['id'],
            service_id,
        )
        previously_published = True
    elif dry_run:
        service_id = str(random.randint(55500000, 55599999))
        get_logger().info(
            "supplier %s: draft %s: dry run: generating random test service id: %s",
            draft_service["supplierId"],
            draft_service['id'],
            service_id,
        )
    else:
        try:
            services = client.publish_draft_service(draft_service['id'], user='publish_draft_services.py')
            service_id = services['services']['id']
            get_logger().info(
                "supplier %s: draft %s: published - new service id: %s",
                draft_service["supplierId"],
                draft_service['id'],
                service_id,
            )

        except dmapiclient.HTTPError as e:
            if e.status_code == 400 and str(e).startswith('Cannot re-publish a submitted service'):
                # re-fetch draft as it clearly doesn't match what we already had
                draft_service = client.get_draft_service(draft_service['id'])
                service_id = draft_service["serviceId"]
                get_logger().warning(
                    "supplier %s: draft %s: failed publishing - has service id: %s",
                    draft_service["supplierId"],
                    draft_service['id'],
                    draft_service['serviceId'],
                )
                previously_published = True
            else:
                raise e

    return service_id, previously_published


def get_draft_services_iter(client, framework_slug, draft_ids_file=None):
    supplier_frameworks = find_suppliers_on_framework(client, framework_slug)

    if draft_ids_file:
        draft_ids = tuple(int(line.strip()) for line in draft_ids_file if line.strip())

        supplier_id_set = frozenset(int(sf["supplierId"]) for sf in supplier_frameworks)

        for draft_id in draft_ids:
            draft_service = client.get_draft_service(draft_id)['services']

            if int(draft_service['supplierId']) not in supplier_id_set:
                raise ValueError(
                    f"Draft service {draft_id}'s supplier ({draft_service['supplierId']}) not on "
                    f"framework {framework_slug!r}"
                )
            if draft_service['frameworkSlug'] != framework_slug:
                raise ValueError(
                    f"Draft service {draft_id} is for framework ({draft_service['frameworkSlug']!r}) not "
                    f"{framework_slug!r}"
                )

            yield draft_service

    else:
        for sf in supplier_frameworks:
            yield from client.find_draft_services_by_framework_iter(
                framework_slug, status='submitted', supplier_id=sf['supplierId']
            )


def publish_draft_services(
    client,
    framework_slug,
    DRAFT_BUCKET,
    DOCUMENTS_BUCKET,
    document_keys,
    _assets_endpoint,
    draft_ids_file=None,
    dry_run=True,
    skip_docs_if_published=True,
    copy_documents=True
):
    for draft_service in get_draft_services_iter(client, framework_slug, draft_ids_file=draft_ids_file):
        service_id, previously_published = publish_draft_service(
            client,
            draft_service,
            dry_run=dry_run,
        )
        if copy_documents and not (skip_docs_if_published and previously_published):
            copy_draft_documents(
                DRAFT_BUCKET,
                DOCUMENTS_BUCKET,
                document_keys,
                _assets_endpoint,
                client,
                framework_slug,
                draft_service,
                service_id,
                dry_run
            )
