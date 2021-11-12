#!/usr/bin/env python
"""
Export a suppliers declaration responses, alongside the questions they answered where available.

Usage:
    scripts/oneoff/export-declaration-responses.py <content_path> <stage> <framework_slug> <supplier_id>
"""
import csv
import sys

from dmapiclient import DataAPIClient
from dmcontent import ContentLoader
from dmcontent.errors import ContentNotFoundError
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token


def get_question(content_loader, framework_slug, question_slug):
    try:
        return content_loader.get_question(framework_slug, 'declaration', question_slug)['question'].render()
    except ContentNotFoundError:
        return question_slug


if __name__ == '__main__':
    arguments = docopt(__doc__)

    client = DataAPIClient(
        get_api_endpoint_from_stage(arguments['<stage>']),
        get_auth_token('api', arguments['<stage>'])
    )
    supplier_id = arguments['<supplier_id>']
    framework_slug = arguments['<framework_slug>']
    content_loader = ContentLoader(arguments['<content_path>'])

    declaration = client.get_supplier_declaration(supplier_id, framework_slug)['declaration']

    declaration_rendered = [
        (get_question(content_loader, framework_slug, question_slug), answer)
        for question_slug, answer in declaration.items() if question_slug != "status"
    ]

    with open(f"{framework_slug}-{supplier_id}-declaration.csv", 'w', newline='') as f:
        writer = csv.writer(f, delimiter=',', quotechar='"')
        writer.writerow(["question", "answer"])
        writer.writerows(declaration_rendered)
