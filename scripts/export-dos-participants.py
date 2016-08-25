#!/usr/bin/env python
"""Export DOS user research participants

Usage:
    scripts/export-dos-participants.py <stage> <api_token> <content_path>
"""
import sys
sys.path.insert(0, '.')

import csv
from docopt import docopt
from dmscripts.env import get_api_endpoint_from_stage
from dmscripts.export_dos_suppliers import (
    FRAMEWORK_SLUG, find_services_by_lot, make_fields_from_content_questions, write_csv
)
from dmapiclient import DataAPIClient
from dmcontent.content_loader import ContentLoader
from dmscripts.logging import configure_logger, WARNING

logger = configure_logger({"dmapiclient": WARNING})


def find_all_participants(client):
    return find_services_by_lot(client, FRAMEWORK_SLUG, "user-research-participants")


def make_row(content_manifest):
    question_ids = ["recruitMethods", "recruitFromList", "locations"]
    questions = [content_manifest.get_question(question_id) for question_id in question_ids]
    for question in questions:
        print(question["id"], question.fields, question.id)

    def inner(record):
        row = [
            ("supplier_id", record["supplier_id"]),
            ("supplier_name", record["supplier"]["name"]),
            ("supplier_declaration_name", record["declaration"].get("nameOfOrganisation", "")),
            ("status", "PASSED" if record["onFramework"] else "FAILED"),
        ]
        return row + make_fields_from_content_questions(questions, record)

    return inner


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    API_TOKEN = arguments['<api_token>']
    CONTENT_PATH = arguments['<content_path>']

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), API_TOKEN)

    content_loader = ContentLoader(CONTENT_PATH)
    content_loader.load_manifest(FRAMEWORK_SLUG, "services", "edit_submission")
    content_manifest = content_loader.get_manifest(FRAMEWORK_SLUG, "edit_submission")

    records = find_all_participants(client)

    write_csv(records,
              make_row(content_manifest),
              "output/dos-user-research-participants.csv")
