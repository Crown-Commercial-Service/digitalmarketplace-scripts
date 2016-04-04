#!/usr/bin/env python
"""Export DOS outcomes

Usage:
    scripts/export-dos-outcomes.py <stage> <api_token> <content_path>
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


def find_all_outcomes(client):
    return find_services_by_lot(client, FRAMEWORK_SLUG, "digital-outcomes")


def make_row(capabilities, locations):
    def inner(record):
        row = [
            ("supplier_id", record["supplier_id"]),
            ("supplier_name", record['supplier']['name']),
            ("supplier_declaration_name", record['declaration'].get('nameOfOrganisation', '')),
            ("status", "PASSED" if record["onFramework"] else "FAILED"),
        ]
        return row + \
            make_fields_from_content_questions(capabilities + locations, record)

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
    API_TOKEN = arguments['<api_token>']
    CONTENT_PATH = arguments['<content_path>']

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), API_TOKEN)

    content_loader = ContentLoader(CONTENT_PATH)
    content_loader.load_manifest(FRAMEWORK_SLUG, "services", "edit_submission")
    content_manifest = content_loader.get_manifest(FRAMEWORK_SLUG, "edit_submission")

    capabilities = get_team_capabilities(content_manifest)
    locations = get_outcomes_locations(content_manifest)
    suppliers = find_all_outcomes(client)

    write_csv(suppliers,
              make_row(capabilities, locations),
              "output/dos-outcomes.csv")
