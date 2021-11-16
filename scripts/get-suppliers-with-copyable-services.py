#!/usr/bin/env python3
"""
For performance testing, we need suppliers who are able to copy services from the previous iteration of the framework.
Get up to 1000 suitable suppliers and then remove their data for the new framework so they're in a clean state for use
in tests.

Usage:
    scripts/get-suppliers-with-copyable-services.py <stage> <new-framework> <copy-from-framework>
"""
import sys

from dmapiclient import DataAPIClient, HTTPError
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt

sys.path.insert(0, ".")

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.updated_by_helpers import get_user

# We don't want to use _all_ the suppliers. There should be ~5000 eligible suppliers.
SUPPLIER_LIMIT = 1000


if __name__ == "__main__":
    arguments = docopt(__doc__)

    data_api_client = DataAPIClient(
        get_api_endpoint_from_stage(arguments['<stage>']), get_auth_token("api", arguments['<stage>']), user=get_user()
    )
    new_framework_slug = arguments['<new-framework>']
    copy_from_framework_slug = arguments['<copy-from-framework>']

    suppliers_on_old_framework = data_api_client.find_framework_suppliers_iter(copy_from_framework_slug)

    for count, supplier in enumerate(suppliers_on_old_framework):
        if count >= SUPPLIER_LIMIT:
            break

        supplier_id = supplier['supplierId']
        for service in data_api_client.find_draft_services_iter(supplier_id, framework=new_framework_slug):
            data_api_client.delete_draft_service(service['id'])

        try:
            data_api_client.remove_supplier_declaration(92197, new_framework_slug)
            data_api_client.set_supplier_framework_application_company_details_confirmed(
                supplier_id, new_framework_slug, False
            )
        except HTTPError as e:
            if not (e.status_code == 404 and "has not registered interest" in e.message):
                raise

        print(supplier_id)
