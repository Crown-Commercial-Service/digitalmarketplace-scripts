#!/usr/bin/env python
"""
Send a reminder email to suppliers who have at least one successful lot entry on the given framework
but who have not yet signed their framework agreement.

Uses the Notify API to send the reminder email. This script *should not* resend emails.

Usage:
    scripts/framework-applications/remind-suppliers-to-sign-framework-agreement.py [options]
         [--supplier-id=<id> ... | --supplier-ids-from=<file>]
         <stage> <framework> <notify_api_key> <content_path>

Example:
    scripts/framework-applications/remind-suppliers-to-sign-framework-agreement.py preview g-cloud-11
        api-key content-path

Parameters:
    <stage>                     Environment to run script against.
    <framework>                 Slug of framework to run script against.
    <notify_api_key>            API key for GOV.UK Notify.
    <content_path>              Path to digitalmarketplace-frameworks repository

Options:
    --supplier-id=<id>          ID(s) of supplier(s) to email.
    --supplier-ids-from=<file>  Path to file containing supplier ID(s), one per line.

    -n, --dry-run               Run script without sending emails.

    -h, --help                  Show this screen.
"""
import sys
from typing import List
from itertools import chain
from docopt import docopt

sys.path.insert(0, '.')

from dmapiclient import DataAPIClient
from dmcontent.content_loader import ContentLoader
from dmscripts.helpers.email_helpers import scripts_notify_client
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.supplier_data_helpers import get_supplier_ids_from_args, get_email_addresses_for_supplier
from dmutils.email.helpers import hash_string
from dmutils.env_helpers import get_api_endpoint_from_stage

NOTIFY_TEMPLATE_ID = "b4c60768-abb8-4fb3-b1f1-09259df7ee11"


def get_supplier_ids_not_signed(api_client: DataAPIClient, framework_slug: str) -> List[int]:
    """
    Get a list of supplier IDs who have at least one successful lot entry but have not signed
    the framework agreement
    """
    return [supplier["supplierId"] for supplier in
            api_client.find_framework_suppliers_iter(framework_slug, agreement_returned=False, with_declarations=False)
            if supplier["onFramework"]]


def get_framework_contract_title(content_path: str, framework_slug: str) -> str:
    """The contract title is different for G-Cloud and DOS. Look up the correct name with the content loader"""
    content_loader = ContentLoader(content_path)
    content_loader.load_messages(framework_slug, ["e-signature"])
    return str(content_loader.get_message(framework_slug, "e-signature", "framework_contract_title"))


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    FRAMEWORK_SLUG = arguments['<framework>']
    NOTIFY_API_KEY = arguments['<notify_api_key>']
    CONTENT_PATH = arguments['<content_path>']
    DRY_RUN = arguments['--dry-run']

    logger = logging_helpers.configure_logger()
    mail_client = scripts_notify_client(NOTIFY_API_KEY, logger=logger)
    api_client = DataAPIClient(base_url=get_api_endpoint_from_stage(STAGE), auth_token=get_auth_token('api', STAGE))
    framework = api_client.get_framework(FRAMEWORK_SLUG).get("frameworks")

    contract_title = get_framework_contract_title(CONTENT_PATH, FRAMEWORK_SLUG)

    supplier_ids = get_supplier_ids_from_args(arguments)
    if supplier_ids is None:
        supplier_ids = get_supplier_ids_not_signed(api_client, FRAMEWORK_SLUG)

    # Flatten list of lists
    email_addresses = list(chain.from_iterable(get_email_addresses_for_supplier(api_client, supplier_id)
                                               for supplier_id in supplier_ids))

    prefix = "[Dry Run] " if DRY_RUN else ""
    user_count = len(email_addresses)

    for count, email in enumerate(email_addresses, start=1):
        logger.info(
            f"{prefix}Sending email to supplier user {count} of {user_count}: {hash_string(email)}"
        )
        if not DRY_RUN:
            mail_client.send_email(
                to_email_address=email,
                template_name_or_id=NOTIFY_TEMPLATE_ID,
                personalisation={
                    "framework_name": framework["name"],
                    "contract_title": contract_title,
                    "framework_slug": FRAMEWORK_SLUG
                }
            )
