from collections import Counter
from functools import partial
from multiprocessing.pool import ThreadPool

from dmapiclient import HTTPError


def get_submitted_drafts(client, framework_slug, supplier_id):
    draft_services = client.find_draft_services_iter(supplier_id, framework=framework_slug)
    submitted_drafts = [draft for draft in draft_services
                        if draft["status"] == "submitted" and not draft.get('serviceId')]
    return submitted_drafts


def set_framework_result(client, framework_slug, supplier_id, result, user):
    """
    :param result: A boolean - True if supplier is on framework, False if not.
    """
    try:
        client.set_framework_result(supplier_id, framework_slug, result, user)
        return "  Result set OK: {} - {}".format(supplier_id, "PASS" if result else "FAIL")
    except HTTPError as e:
        return "  Error inserting result for {} ({}): {}".format(supplier_id, result, str(e))


def has_supplier_submitted_services(client, framework_slug, supplier_id):
    submitted_drafts = get_submitted_drafts(client, framework_slug, supplier_id)
    if len(submitted_drafts) > 0:
        return True
    else:
        return False


def find_suppliers_on_framework(client, framework_slug):
    return (
        supplier for supplier in client.find_framework_suppliers(framework_slug)['supplierFrameworks']
        if supplier['onFramework']
    )


def find_suppliers_with_details_and_draft_services(client, framework_slug, supplier_ids=None, lot=None, statuses=None):
    pool = ThreadPool(3)

    records = find_suppliers(client, framework_slug, supplier_ids)
    records = pool.imap(partial(add_supplier_info, client), records)
    records = pool.imap(partial(add_framework_info, client, framework_slug), records)
    records = pool.imap(partial(add_draft_services, client, framework_slug, lot=lot, statuses=statuses), records)
    records = filter(lambda record: len(record["services"]) > 0, records)
    return records


def find_suppliers_with_details_and_draft_service_counts(client, framework_slug, supplier_ids=None):
    pool = ThreadPool(3)

    records = find_suppliers(client, framework_slug, supplier_ids)
    records = pool.imap(partial(add_supplier_info, client), records)
    records = pool.imap(partial(add_framework_info, client, framework_slug), records)
    records = pool.imap(partial(add_draft_counts, client, framework_slug), records)
    return records


def find_suppliers(client, framework_slug, supplier_ids=None):
    suppliers = client.get_interested_suppliers(framework_slug)['interestedSuppliers']
    return ({'supplier_id': supplier_id} for supplier_id in suppliers
            if (supplier_ids is None) or (supplier_id in supplier_ids))


def add_supplier_info(client, record):
    supplier = client.get_supplier(record['supplier_id'])
    return dict(record, supplier=supplier['suppliers'])


def add_framework_info(client, framework_slug, record):
    supplier_framework = client.get_supplier_framework_info(record['supplier_id'], framework_slug)['frameworkInterest']
    return dict(record,
                onFramework=supplier_framework['onFramework'],
                declaration=supplier_framework['declaration'] or {},
                countersignedPath=supplier_framework['countersignedPath'] or "",
                countersignedAt=supplier_framework['countersignedAt'] or "",
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
