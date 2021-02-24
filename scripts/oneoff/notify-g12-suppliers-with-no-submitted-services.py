#!/usr/bin/env python
"""
Send an email to suppliers involved in the G12 recovery process who didn't complete any draft services

Usage:
    notify-g12-suppliers-with-no-submitted-services.py <stage> <notify_api_key> [--dry-run]

Parameters:
    <stage>                     Environment to run script against.
    <notify_api_key>            API key for GOV.UK Notify
Options:
    -h --help                   Show this screen.
    --dry-run                   If set, fetch data for G12 suppliers but don't send emails

Before running this script, ensure that the list of suppliers and draft IDs in the credentials repo is correct.
"""
import sys
import logging
from typing import Dict, List

from dmapiclient import DataAPIClient
from dmutils.email.helpers import hash_string
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt

sys.path.insert(0, ".")

from dmscripts.helpers.auth_helpers import (
    get_g12_suppliers,
    get_auth_token,
    get_g12_recovery_draft_ids,
)
from dmscripts.helpers.email_helpers import scripts_notify_client
from dmscripts.helpers.supplier_data_helpers import get_email_addresses_for_supplier

NOTIFY_TEMPLATE_ID = "7ff14f15-b869-49b1-b2cc-a576fb054a45"


def get_drafts_for_suppliers(api_client, supplier_ids, draft_ids) -> Dict[int, List[dict]]:
    drafts_for_suppliers = {supplier_id: [] for supplier_id in supplier_ids}
    for draft_id in draft_ids:
        draft = api_client.get_draft_service(draft_id)["services"]
        drafts_for_suppliers[draft["supplierId"]].append(draft)
    return drafts_for_suppliers


if __name__ == "__main__":
    args = docopt(__doc__)

    stage = args["<stage>"]
    dry_run = args["--dry-run"]
    notify_api_key = args["<notify_api_key>"]

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("dmapiclient").setLevel(logging.WARNING)
    logging.getLogger("notifications").setLevel(logging.WARNING)
    logger = logging.getLogger()

    notify_client = scripts_notify_client(notify_api_key, logger=logger)
    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token("api", stage),
    )

    prefix = "[Dry Run] " if dry_run else ""
    draft_ids = get_g12_recovery_draft_ids(stage)
    supplier_ids = get_g12_suppliers(stage)

    logging.info(f"Getting G12 draft service data for {stage}")
    drafts_for_suppliers = get_drafts_for_suppliers(data_api_client, supplier_ids, draft_ids)

    for supplier_id in supplier_ids:
        submitted_draft_count = len(
            [
                draft
                for draft in drafts_for_suppliers[supplier_id]
                if draft["status"] == "submitted"
            ]
        )
        logger.info(
            f"{prefix}Supplier {supplier_id} has {submitted_draft_count} submitted services"
        )

        if submitted_draft_count == 0:
            # Only email suppliers who haven't submitted any draft services
            supplier_email_addresses = get_email_addresses_for_supplier(data_api_client, supplier_id)
            if dry_run:
                logging.info(f"{prefix}Skipping sending emails for {len(supplier_email_addresses)} users")

            else:
                logging.info(f"{prefix}Emailing {len(supplier_email_addresses)} supplier users")

                for email in supplier_email_addresses:
                    logging.info(f"{prefix}Sending email to supplier user {hash_string(email)}")
                    notify_client.send_email(
                        to_email_address=email,
                        template_name_or_id=NOTIFY_TEMPLATE_ID,
                        personalisation={
                            "framework_name": "G-Cloud 12"
                        }
                    )
