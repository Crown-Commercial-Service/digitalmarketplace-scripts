from dmapiclient import HTTPError


def get_submitted_drafts(client, framework_slug, supplier_id):
    services = client.find_draft_services(supplier_id, framework=framework_slug)
    services = services["services"]
    submitted_services = [service for service in services if service["status"] == "submitted"]
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
