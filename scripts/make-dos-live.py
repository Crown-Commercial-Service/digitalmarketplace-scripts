"""

Usage:
    scripts/make-dos-live.py <stage> <api_token> [--dry-run]
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.helpers.env import get_api_endpoint_from_stage
from dmscripts.framework_utils import find_suppliers_on_framework
from dmapiclient import DataAPIClient


def find_submitted_draft_services(client, supplier_id, framework_slug):
    return (
        draft for draft in
        client.find_draft_services(supplier_id, framework=framework_slug)['services']
        if draft['status'] == "submitted" and not draft.get("serviceId")
    )


def make_draft_service_live(client, draft, dry_run):
    print(u"  > Migrating draft {} - {}".format(draft['id'], draft['lot']))
    if dry_run:
        print("    > no-op")
    else:
        try:
            services = client.publish_draft_service(draft['id'], "make dos live script")
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
    FRAMEWORK_SLUG = "digital-outcomes-and-specialists"

    api_url = get_api_endpoint_from_stage(STAGE)
    client = DataAPIClient(api_url, arguments['<api_token>'])

    suppliers = find_suppliers_on_framework(client, FRAMEWORK_SLUG)

    for supplier in suppliers:
        print(u"Migrating drafts for supplier {} - {}".format(supplier['supplierId'], supplier['supplierName']))
        drafts = find_submitted_draft_services(client, supplier['supplierId'], FRAMEWORK_SLUG)

        for draft in drafts:
            make_draft_service_live(client, draft, DRY_RUN)
