
import sys
import dmapiclient

sys.path.insert(0, '.')  # noqa
from dmutils.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.framework_helpers import get_full_framework_slug
from dmscripts.helpers.user_helpers import (
    get_random_buyer_with_brief,
    get_supplier_id,
    get_random_user,
)


def get_user(api_url, api_token, stage, role, framework, lot, *, brief_status=None):
    if not api_url:
        api_url = get_api_endpoint_from_stage(stage)

    api_token = api_token or get_auth_token('api', stage)
    api_client = dmapiclient.DataAPIClient(api_url, api_token)

    if role == 'supplier' and framework is not None:
        framework = get_full_framework_slug(framework)
        print('Framework: {}'.format(framework))
        if lot is not None:
            print('Lot: {}'.format(lot))
        supplier_id = get_supplier_id(api_client, framework, lot)
        print('Supplier id: {}'.format(supplier_id))
        return get_random_user(api_client, None, supplier_id)
    if role == "buyer" and framework is not None:
        framework = get_full_framework_slug(framework)
        print('Framework: {}'.format(framework))
        if framework.startswith("digital-outcomes-and-specialists"):
            print(f"Has requirements: {brief_status or 'True'}")
            return get_random_buyer_with_brief(api_client, framework, lot, brief_status=brief_status)
    else:
        return get_random_user(api_client, role)
