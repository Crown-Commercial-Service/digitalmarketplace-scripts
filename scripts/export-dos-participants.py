#!/usr/bin/env python3
"""

For a DOS-type framework this will export details of all "user-research-participants" services, including the
recruitment methods the supplier provides and the locations they can provide them in.

Usage:
    scripts/export-dos-participants.py <stage> <framework_slug> <content_path>
"""
from multiprocessing.pool import ThreadPool
import sys
sys.path.insert(0, '.')

from dmscripts.helpers.csv_helpers import make_fields_from_content_questions
from dmscripts.helpers.framework_helpers import find_suppliers_with_details_and_draft_services

from docopt import docopt
from dmscripts.helpers.csv_helpers import write_csv_with_make_row
from dmscripts.helpers.auth_helpers import get_auth_token
from dmapiclient import DataAPIClient
from dmcontent.content_loader import ContentLoader
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging
from dmutils.env_helpers import get_api_endpoint_from_stage

logger = logging_helpers.configure_logger({"dmapiclient": logging.WARNING})


def find_all_participants(client, map_impl=map):
    return find_suppliers_with_details_and_draft_services(client,
                                                          FRAMEWORK_SLUG,
                                                          lot="user-research-participants",
                                                          statuses="submitted",
                                                          map_impl=map_impl,
                                                          )


def make_row(content_manifest):
    question_ids = ["recruitMethods", "recruitFromList", "locations"]
    questions = [content_manifest.get_question(question_id) for question_id in question_ids]


    def inner(record):
        row = [
            ("supplier_id", record["supplier_id"]),
            ("supplier_name", record["supplier"]["name"]),
            ("supplier_declaration_name", record["declaration"].get("supplierRegisteredName", "")),
            ("status", "PASSED" if record["onFramework"] else "FAILED"),
        ]
        return row + make_fields_from_content_questions(questions, record)

    return inner


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    CONTENT_PATH = arguments['<content_path>']
    FRAMEWORK_SLUG = arguments['<framework_slug>']

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), get_auth_token('api', STAGE))

    content_loader = ContentLoader(CONTENT_PATH)
    content_loader.load_manifest(FRAMEWORK_SLUG, "services", "edit_submission")
    content_manifest = content_loader.get_manifest(FRAMEWORK_SLUG, "edit_submission")

    pool = ThreadPool(3)

    records = find_all_participants(client, map_impl=pool.imap)

    write_csv_with_make_row(
        records,
        make_row(content_manifest),
        "output/{}-user-research-participants.csv".format(FRAMEWORK_SLUG)
    )
