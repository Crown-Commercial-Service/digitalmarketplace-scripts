#!/usr/bin/env python3
"""

For a DOS-type framework this will export details of all "digital-specialists" services, including the
specialist roles the supplier provides, the locations they can provide them in and the min and max prices per role.

Usage:
    scripts/export-dos-specialists.py <stage> <framework_slug> <content_path> [options]

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
from dmscripts.helpers.csv_helpers import make_fields_from_content_questions, write_csv_with_make_row
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.framework_helpers import find_suppliers_with_details_and_draft_services
from dmapiclient import DataAPIClient
from dmcontent.content_loader import ContentLoader
from dmscripts.helpers import logging_helpers
from dmutils.env_helpers import get_api_endpoint_from_stage


def find_all_specialists(client, map_impl=map):
    return find_suppliers_with_details_and_draft_services(client,
                                                          FRAMEWORK_SLUG,
                                                          lot="digital-specialists",
                                                          statuses="submitted",
                                                          map_impl=map_impl,
                                                          )


def make_row(content_manifest):
    section = content_manifest.get_section("individual-specialist-roles")
    specialist_roles = list(get_specialist_roles(section))

    def inner(record):
        row = [
            ("supplier_id", record["supplier_id"]),
            ("supplier_name", record['supplier']['name']),
            ("supplier_declaration_name", record['declaration'].get('supplierRegisteredName', '')),
            ("status", "PASSED" if record["onFramework"] else "FAILED"),
        ]
        return row + make_fields_from_content_questions(specialist_roles, record)

    return inner


def get_specialist_roles(section):
    return [
        question
        for outer_question in section.questions
        for question in outer_question.questions
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

    pool = ThreadPool(3)

    logger.info(f"Finding Digital Specialists suppliers for {FRAMEWORK_SLUG}")
    suppliers = find_all_specialists(client, map_impl=pool.imap)

    logger.info(f"Building CSV for {len(suppliers)} Digital Specialists suppliers")
    write_csv_with_make_row(
        suppliers,
        make_row(content_manifest),
        os.path.join(OUTPUT_DIR, "digital-specialists-suppliers.csv".format(FRAMEWORK_SLUG)),
        include_last_updated=True
    )
