"""

For a DOS-style framework (with no documents to migrate) this will:
 1. Find all suppliers awarded onto the framework
 2. Find all their submitted draft services on the framework
 3. Migrate these from drafts to "real" services

Usage:
    scripts/publish-dos-draft-services.py <framework_slug> <stage> [--dry-run]
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.framework_helpers import find_suppliers_on_framework, get_submitted_drafts
from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage


def make_draft_service_live(client, draft, dry_run):
    print(u"  > Migrating draft {} - {}".format(draft['id'], draft['lot']))
    if dry_run:
        print("    > no-op")
    else:
        try:
            services = client.publish_draft_service(draft['id'], "publish dos draft services script")
            service_id = services['services']['id']
            print(u"    > draft service published - new service ID {}".format(service_id))
        except Exception as e:
            if e.message == "Cannot re-publish a submitted service":
                print(u"    > Draft {} already published".format(draft['id']))
            else:
                print(u"    > ERROR MIGRATING DRAFT {} - {}".format(draft['id'], e.message))


if __name__ == "__main__":
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    DRY_RUN = arguments['--dry-run']
    FRAMEWORK_SLUG = arguments['<framework_slug>']

    api_url = get_api_endpoint_from_stage(STAGE)
    client = DataAPIClient(api_url, get_auth_token('api', STAGE))

    suppliers = find_suppliers_on_framework(client, FRAMEWORK_SLUG)

    for supplier in suppliers:
        print(u"Migrating drafts for supplier {} - {}".format(supplier['supplierId'], supplier['supplierName']))
        draft_services = get_submitted_drafts(client, FRAMEWORK_SLUG, supplier['supplierId'])

        for draft_service in draft_services:
            make_draft_service_live(client, draft_service, DRY_RUN)
