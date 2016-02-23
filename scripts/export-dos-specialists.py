#!/usr/bin/env python
"""Export DOS specialists

Export DOS specialists as a CSV for manual review.

Usage:
    scripts/export-dos-specialists.py <stage> <api_token> <content_path>
"""
import sys
sys.path.insert(0, '.')

from multiprocessing.pool import ThreadPool
import itertools
import os
import csv

from docopt import docopt
from dmscripts.env import get_api_endpoint_from_stage
from dmscripts.export_dos_suppliers import (
    find_services_by_lot, FRAMEWORK_SLUG, make_fields_from_content_questions, write_csv
)
from dmapiclient import DataAPIClient
from dmutils.content_loader import ContentLoader
from dmscripts.logging import configure_logger, WARNING

logger = configure_logger({"dmapiclient": WARNING})


def find_all_specialists(client):
    return find_services_by_lot(client, FRAMEWORK_SLUG, "digital-specialists")


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

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), API_TOKEN)

    content_loader = ContentLoader(CONTENT_PATH)
    content_loader.load_manifest(FRAMEWORK_SLUG, "services", "edit_submission")
    content_manifest = content_loader.get_manifest(FRAMEWORK_SLUG, "edit_submission")

    suppliers = find_all_specialists(client)

    write_csv(suppliers,
              make_row(content_manifest),
              "output/dos-specialists.csv")
