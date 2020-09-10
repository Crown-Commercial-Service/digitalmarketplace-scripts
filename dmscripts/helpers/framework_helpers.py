from typing import Iterable, Mapping

from collections import Counter
from functools import partial
import logging
import re

from dmapiclient import DataAPIClient, HTTPError

logger = logging.getLogger("framework_helpers")


def set_framework_result(client, framework_slug, supplier_id, result, user):
    """
    :param result: A boolean - True if supplier is on framework, False if not.
    """
    try:
        client.set_framework_result(supplier_id, framework_slug, result, user)
        return "  Result set OK: {} - {}".format(supplier_id, "PASS" if result else "FAIL")
    except HTTPError as e:
        return "  Error inserting result for {} ({}): {}".format(supplier_id, result, str(e))


def find_suppliers_on_framework(client: DataAPIClient, framework_slug: str) -> Iterable[Mapping]:
    return (
        supplier_framework
        for supplier_framework in client.find_framework_suppliers_iter(framework_slug, with_declarations=None)
        if supplier_framework['onFramework']
    )


def find_suppliers_with_details_and_draft_services(
    client,
    framework_slug,
    supplier_ids=None,
    lot=None,
    statuses=None,
    map_impl=map,
):
    records = find_suppliers(client, framework_slug, supplier_ids)
    records = map_impl(partial(add_supplier_info, client), records)
    records = map_impl(partial(add_framework_info, client, framework_slug), records)
    records = map_impl(partial(add_draft_services, client, framework_slug, lot=lot, statuses=statuses), records)
    records = [record for record in records if len(record["services"]) > 0]
    return records


def framework_supports_e_signature(framework_slug):
    """
    This is a hacky way to determine if a framework supports e-signature,
    which will be frameworks from G-Cloud-12 onwards
    # TODO: Do more robust check
    :param framework_slug:
    :return: Boolean
    """
    return framework_slug in ['g-cloud-12']


def find_suppliers_with_details_and_draft_service_counts(
    client,
    framework_slug,
    supplier_ids=None,
    map_impl=map,
):
    records = find_suppliers(client, framework_slug, supplier_ids)
    length = len(records)
    records = map_impl(partial(add_supplier_info, client), records)
    records = map_impl(partial(add_framework_info, client, framework_slug), records)
    records = map_impl(partial(add_agreement_info, client), records)
    records = map_impl(partial(add_draft_counts, client, framework_slug), records)
    records = map_watch(
        records,
        f"fetched details and draft counts for supplier {{count}}/{length}"
    )
    return records


def find_suppliers(client, framework_slug, supplier_ids=None):
    suppliers = client.get_interested_suppliers(framework_slug)['interestedSuppliers']
    suppliers = [
        {'supplier_id': supplier_id} for supplier_id in suppliers
        if (supplier_ids is None) or (supplier_id in supplier_ids)
    ]
    logger.debug(f"found {len(suppliers)} suppliers interested in '{framework_slug}'")
    return suppliers


def add_supplier_info(client, record):
    supplier = client.get_supplier(record['supplier_id'])
    return dict(record, supplier=supplier['suppliers'])


def add_framework_info(client, framework_slug, record):
    supplier_framework = client.get_supplier_framework_info(record['supplier_id'], framework_slug)['frameworkInterest']
    return dict(record,
                onFramework=supplier_framework['onFramework'],
                frameworkSlug=supplier_framework['frameworkSlug'],
                declaration=supplier_framework['declaration'] or {},
                countersignedPath=supplier_framework['countersignedPath'] or "",
                countersignedAt=supplier_framework['countersignedAt'] or "",
                agreementId=supplier_framework['agreementId'] or ""
                )


def add_agreement_info(client, record):
    framework_agreement_id = record['agreementId']
    framework_agreement = client.get_framework_agreement(framework_agreement_id)
    return dict(record,
                signerName=framework_agreement['agreement']['signedAgreementDetails']['signerName'] or "",
                signerRole=framework_agreement['agreement']['signedAgreementDetails']['signerRole'] or "",
                signedAgreementReturnedAt=framework_agreement['agreement']['signedAgreementReturnedAt'] or ""
                )


def add_draft_services(client, framework_slug, record, lot=None, statuses=None):
    drafts = client.find_draft_services(record["supplier_id"], framework=framework_slug)
    drafts = [
        draft for draft in drafts["services"]
        if (not lot or draft["lotSlug"] == lot) and (not statuses or draft["status"] in statuses)
    ]
    return dict(record, services=drafts)


def add_draft_counts(client, framework_slug, record):
    # "counts" is a counter of (lotSlug, status) tuples
    counts = Counter(
        (ds['lotSlug'], ds['status'])
        for ds in client.find_draft_services_iter(record['supplier']['id'], framework=framework_slug)
    )
    return dict(record, counts=counts)


def get_full_framework_slug(framework):
    iteration = re.search(r'(\d+)', framework)
    if framework.startswith('g'):
        prefix = 'g-cloud'
    elif framework.startswith('d'):
        prefix = 'digital-outcomes-and-specialists'
    else:
        return framework

    if iteration:
        return "{}-{}".format(prefix, iteration.group(1))
    else:
        return prefix


def map_watch(iterable, msg_format=None):
    """Prints a debug message when you fetch an element from a list

    :iterable:      a list (or tuple, generator) of items that you want to process
    :msg_format:    message to emit to debug logger

    :returns:       a generator that produces elements and emits a debug
                    message while doing so
    """
    count = 0

    if msg_format is None:
        msg_format = "processing record {count}"

    for e in iterable:
        yield e
        count += 1
        logger.debug(msg_format.format(count=count))
