#!/usr/bin/env python
"""

For a DOS-type framework this will export details of all "digital-specialists" services, including the
specialist roles the supplier provides, the locations they can provide them in and the min and max prices per role.

Usage:
    scripts/export-dos-specialists.py <stage> <api_token> <framework_slug> <content_path>
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.helpers.csv_helpers import make_fields_from_content_questions, write_csv
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers.framework_helpers import find_suppliers_with_details_and_draft_services
from dmapiclient import DataAPIClient
from dmcontent.content_loader import ContentLoader
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging

logger = logging_helpers.configure_logger({"dmapiclient": logging.WARNING})


def find_all_specialists(client):
    return find_suppliers_with_details_and_draft_services(client,
                                                          FRAMEWORK_SLUG,
                                                          lot="digital-specialists",
                                                          statuses="submitted"
                                                          )


def make_row(content_manifest):
    section = content_manifest.get_section("individual-specialist-roles")
    specialist_roles = list(get_specialist_roles(section))

    def inner(record):
        row = [
            ("supplier_id", record["supplier_id"]),
            ("supplier_name", record['supplier']['name']),
            ("supplier_declaration_name", record['declaration'].get('nameOfOrganisation', '')),
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
    API_TOKEN = arguments['<api_token>']
    CONTENT_PATH = arguments['<content_path>']
    FRAMEWORK_SLUG = arguments['<framework_slug>']

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), API_TOKEN)

    content_loader = ContentLoader(CONTENT_PATH)
    content_loader.load_manifest(FRAMEWORK_SLUG, "services", "edit_submission")
    content_manifest = content_loader.get_manifest(FRAMEWORK_SLUG, "edit_submission")

    suppliers = find_all_specialists(client)

    write_csv(suppliers,
              make_row(content_manifest),
              "output/{}-specialists.csv".format(FRAMEWORK_SLUG))
