#!/usr/bin/env python3
"""

For a DOS-type framework this will export details of all "digital-outcomes" services, including the types
of outcome the supplier provides and the locations they can provide them in.

Usage:
    scripts/export-dos-outcomes.py <stage> <framework_slug> <content_path> [options]

Options:
    -v --verbose                Print INFO level messages.
    --output-dir=<output_dir>   Directory to write csv files to [default: output]
"""
from multiprocessing.pool import ThreadPool
import os
import sys
sys.path.insert(0, '.')

import logging
from docopt import docopt

from dmapiclient import DataAPIClient
from dmcontent.content_loader import ContentLoader

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.csv_helpers import make_fields_from_content_questions, write_csv_with_make_row
from dmscripts.helpers.framework_helpers import find_suppliers_with_details_and_draft_services
from dmscripts.helpers import logging_helpers
from dmutils.env_helpers import get_api_endpoint_from_stage


def find_all_outcomes(client, map_impl=map):
    return find_suppliers_with_details_and_draft_services(client,
                                                          FRAMEWORK_SLUG,
                                                          lot="digital-outcomes",
                                                          statuses="submitted",
                                                          map_impl=map_impl,
                                                          )


def make_row(capabilities, locations):
    def inner(record):
        row = [
            ("supplier_id", record["supplier_id"]),
            ("supplier_name", record['supplier']['name']),
            ("supplier_declaration_name", record['declaration'].get('supplierRegisteredName', '')),
            ("status", "PASSED" if record["onFramework"] else "FAILED"),
        ]
        return row + make_fields_from_content_questions(capabilities + locations, record)

    return inner


def get_team_capabilities(content_manifest):
    section = content_manifest.get_section("team-capabilities")

    return [
        question.questions[0]
        for question in section.questions
    ]


def get_outcomes_locations(content_manifest):
    return [
        content_manifest.get_question("locations")
    ]


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    CONTENT_PATH = arguments['<content_path>']
    FRAMEWORK_SLUG = arguments['<framework_slug>']
    OUTPUT_DIR = arguments['--output-dir']
    verbose = arguments['--verbose']

    logger = logging_helpers.configure_logger(
        {"dmapiclient": logging.INFO} if verbose else {"dmapiclient": logging.WARN}
    )

    if not os.path.exists(OUTPUT_DIR):
        logger.info("Creating {} directory".format(OUTPUT_DIR))
        os.makedirs(OUTPUT_DIR)

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), get_auth_token('api', STAGE))

    content_loader = ContentLoader(CONTENT_PATH)
    content_loader.load_manifest(FRAMEWORK_SLUG, "services", "edit_submission")
    content_manifest = content_loader.get_manifest(FRAMEWORK_SLUG, "edit_submission")

    capabilities = get_team_capabilities(content_manifest)
    locations = get_outcomes_locations(content_manifest)

    pool = ThreadPool(3)

    logger.info(f"Finding suppliers for Digital Outcomes on {FRAMEWORK_SLUG}")
    suppliers = find_all_outcomes(client, map_impl=pool.imap)

    logger.info(f"Building CSV for {len(suppliers)} Digital Outcomes suppliers")
    write_csv_with_make_row(
        suppliers,
        make_row(capabilities, locations),
        os.path.join(OUTPUT_DIR, "digital-outcomes-suppliers.csv".format(FRAMEWORK_SLUG)),
        include_last_updated=True
    )
