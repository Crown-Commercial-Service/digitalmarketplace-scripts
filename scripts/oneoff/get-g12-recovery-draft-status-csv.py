#!/usr/bin/env python
"""
Export the status of the G12 recovery draft services to a CSV, so they can
be evaluated by CCS.

Usage: ./scripts/oneoff/get-g12-recovery-draft-status-csv.py [--stage=<st>] [--filename=<file>]

Options:
    --stage=<st>            Optional. The stage to target. Must be one of 'preview', 'staging' or 'production'.
                                Defaults to 'production'
    --filename=<file>       Optional. The output filename to use. Defaults to 'g12_recovery_draft_services.csv'
"""

import csv
import sys
import logging
from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt

sys.path.insert(0, ".")

from dmscripts.helpers.auth_helpers import get_auth_token, get_g12_recovery_draft_ids

if __name__ == "__main__":
    args = docopt(__doc__)

    stage = args.get("<st>") or 'production'
    filename = args.get("<file>") or "g12_recovery_draft_services.csv"
    column_headers = [
        "supplier_name", "supplier_id", "lot", "draft_service_name", "draft_service_id", "draft_service_status"
    ]

    api_client = DataAPIClient(
        get_api_endpoint_from_stage(stage),
        get_auth_token("api", stage),
    )
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('dmapiclient').setLevel(logging.WARNING)

    with open(filename, "w") as f:
        writer = csv.DictWriter(f, column_headers)
        logging.info(f"Fetching G12 recovery draft IDs for {stage}")

        for draft_id in get_g12_recovery_draft_ids(stage):
            logging.info(f"Fetching data for draft {draft_id} on {stage}")
            draft = api_client.get_draft_service(draft_id)["services"]
            writer.writerow(
                {
                    "supplier_name": draft["supplierName"],
                    "supplier_id": draft["supplierId"],
                    "lot": draft["lotName"],
                    "draft_service_name": draft["serviceName"],
                    "draft_service_id": draft_id,
                    "draft_service_status": draft["status"]
                }
            )
