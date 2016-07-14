from dmapiclient import HTTPError


def set_framework_result(client, framework_slug, supplier_id, result, user):
    try:
        client.set_framework_result(supplier_id, framework_slug, result, user)
        return "  Result set OK: {} - {}".format(supplier_id, "PASS" if result else "FAIL")
    except HTTPError as e:
        return "  Error inserting result for {} ({}): {}".format(supplier_id, result, str(e))
