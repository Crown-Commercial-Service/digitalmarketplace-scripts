from dmapiclient import HTTPError


def get_submitted_drafts(client, framework_slug, supplier_id):
    draft_services = client.find_draft_services_iter(supplier_id, framework=framework_slug)
    submitted_services = [service for service in draft_services if service["status"] == "submitted"
                          and not service.get('serviceId')]
    return submitted_services


def set_framework_result(client, framework_slug, supplier_id, result, user):
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
