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
    find_suppliers, add_supplier_info, FRAMEWORK_SLUG, add_framework_info,
    add_services, make_field_label_counts
)
from dmapiclient import DataAPIClient
from dmutils.content_loader import ContentLoader


def find_all_outcomes(client):
    pool = ThreadPool(20)
    records = find_suppliers(client, FRAMEWORK_SLUG)
    records = pool.imap(add_supplier_info(client), records)
    records = pool.imap(add_framework_info(client, FRAMEWORK_SLUG), records)
    # records = filter(lambda record: record['onFramework'], records)
    records = pool.imap(
        add_services(client, FRAMEWORK_SLUG,
                     lot="digital-outcomes",
                     status="submitted"),
        records)
    records = filter(lambda record: len(record["services"]) > 0, records)

    return records


def make_row(record, capabilities, locations):
    row = [
        ("supplier_id", record["supplier_id"]),
        ("supplier_name", record['supplier']['name']),
        ("supplier_declaration_name", record['declaration'].get('nameOfOrganisation', '')),
        ("status", "PASSED" if record["onFramework"] else "FAILED"),
    ]
    return row + \
        make_field_label_counts(capabilities, record) + \
        make_field_label_counts(locations, record)


def fieldnames(row):
    return [f[0] for f in row]


def write_csv(records, capabilities, locations, filename):
    writer = None

    with open(filename, "w+") as f:
        for record in records:
            sys.stdout.write(".")
            sys.stdout.flush()
            row = make_row(record, capabilities, locations)
            if writer is None:
                writer = csv.DictWriter(f, fieldnames=fieldnames(row))
                writer.writeheader()
            writer.writerow(dict(row))


def get_team_capabilities(content_manifest):
    section = content_manifest.get_section("team-capabilities")

    return [
        {
            "label": option["label"],
            "id": question.questions[0]["id"],
        }
        for question in section.questions
        for option in question.questions[0].options
    ]


def get_outcomes_locations(content_manifest):
    question = content_manifest.get_question("outcomesLocations")
    return [
        {
            "label": option["label"],
            "id": question["id"],
        }
        for option in question.options
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

    write_csv(suppliers, capabilities, locations,
              "output/dos-outcomes.csv")
