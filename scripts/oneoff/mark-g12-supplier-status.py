#!/usr/bin/env python
"""
We have one supplier in the G12 recovery process who has not yet signed the framework agreement. In order for them
to do this, we need to evaluate their answers to the declaration questions and mark them as being on G-Cloud 12 if
they pass.

This script borrows heavily from
digitalmarketplace-scripts/blob/master/scripts/framework-applications/mark-definite-framework-results.py
to do so for this single supplier.

Usage: mark-g12-supplier-status.py <stage> --updated-by=<updater> --dry-run
"""
import sys
import logging
import json
from docopt import docopt
from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage
sys.path.insert(0, ".")

from dmscripts.mark_definite_framework_results import _passes_validation, pass_supplier
from dmscripts.helpers.auth_helpers import get_auth_token

UNSIGNED_SUPPLIER_ID = 712034
FRAMEWORK_SLUG = "g-cloud-12"

if __name__ == "__main__":
    args = docopt(__doc__)
    stage = args["<stage>"]
    updater = args["updater"]
    dry_run = args["--dry-run"]

    api_client = DataAPIClient(
        get_api_endpoint_from_stage(stage),
        get_auth_token("api", stage),
    )

    logging.basicConfig(level=logging.INFO)
    logging.getLogger('dmapiclient').setLevel(logging.WARNING)
    logger = logging.getLogger()

    prefix = "[DRY RUN] " if dry_run else ""

    # Check the supplier's answers to the declaration questions against the validation schema
    declaration_definite_pass_schema = json.load(open(f"schemas/{FRAMEWORK_SLUG}-assessment-schema.json", "r"))

    declaration_discretionary_pass_schema = \
        (declaration_definite_pass_schema.get("definitions") or {}).get("baseline")

    supplier_framework = api_client.get_supplier_framework_info(
        UNSIGNED_SUPPLIER_ID,
        FRAMEWORK_SLUG
    )["frameworkInterest"]

    if supplier_framework["onFramework"] is True:
        logger.info(f"{prefix}Skipping: already passed")

    # Check for a definite pass
    # mark-definite-framework-results.py also checks that they have a valid service, but we already
    # know this supplier has submitted a service
    supplier_passes_validation = _passes_validation(
        supplier_framework["declaration"],
        declaration_definite_pass_schema,
        logger,
        schema_name="declaration_definite_pass_schema",
        tablevel=1
    )
    if supplier_passes_validation:
        # Congratulations supplier, you pass!
        logger.info(f"{prefix}Marked supplier {UNSIGNED_SUPPLIER_ID} as on {FRAMEWORK_SLUG}!")
        if not dry_run:
            pass_supplier(UNSIGNED_SUPPLIER_ID, FRAMEWORK_SLUG, updater,
                          supplier_framework, api_client, logger, dry_run)

    else:
        # Our supplier hasn't passed validation. Log an error because we probably need to talk to CCS about
        # what to do in this case.
        logger.error(
            f"{prefix}Supplier {UNSIGNED_SUPPLIER_ID}'s declaration answers have failed automatic validation.",
            "We should export their answers and ask CCS for clarification on what to do next."
        )
