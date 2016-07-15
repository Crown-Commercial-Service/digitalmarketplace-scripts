#!/usr/bin/env python
"""Generate framework agreement signature pages from supplier "about you" information for suppliers
who applied to a framework.

Currently will only work for framework_slug=g-cloud-8.

To add support for future frameworks we will will need to add to the LOTS and DECLARATION_FIELDS in
dmscripts/export_framework_applicant_details.py

Usage:
    scripts/generate-g8-signature-pages.py <stage> <api_token> <framework_slug> <template_folder>

Example:
    scripts/generate-g8-signature-pages.py dev myToken g-cloud-8 ../digitalmarketplace-agreements/documents/g-cloud

"""
import sys
import os
import csv
import io

sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.env import get_api_endpoint_from_stage
from dmscripts.export_framework_applicant_details import find_suppliers_with_details
from dmscripts.generate_agreement_signature_pages import render_html_for_all_suppliers
from dmapiclient import DataAPIClient
from dmscripts import logging


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    API_TOKEN = arguments['<api_token>']
    FRAMEWORK = arguments['<framework_slug>']
    TEMPLATE_FOLDER = arguments['<template_folder>']

    repo_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..'))
    output_dir = os.path.join(repo_root, 'output')

    logger = logging.configure_logger()

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), API_TOKEN)

    headers, rows = find_suppliers_with_details(client, FRAMEWORK)

    render_html_for_all_suppliers(rows, FRAMEWORK, TEMPLATE_FOLDER, output_dir)
