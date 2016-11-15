#!/usr/bin/env python
"""Generate framework agreement signature pages from supplier "about you" information for suppliers
who applied to a framework.

Currently will only work for framework_slug=g-cloud-8.

To add support for future frameworks we will will need to add to the LOTS and DECLARATION_FIELDS in
dmscripts/export_framework_applicant_details.py

Usage:
    scripts/generate-agreement-signature-pages.py <stage> <api_token> <framework_slug> <template_folder> <output_folder>

Example:
    generate-agreement-signature-pages.py dev myToken g-cloud-8 ../digitalmarketplace-agreements/documents/g-cloud pdfs

"""
import sys
import os
import shutil

sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.env import get_api_endpoint_from_stage
from dmscripts.export_framework_applicant_details import find_suppliers_with_details
from dmscripts.generate_agreement_signature_pages import render_html_for_successful_suppliers, \
    render_pdf_for_each_html_page
from dmapiclient import DataAPIClient
from dmscripts import logging


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    API_TOKEN = arguments['<api_token>']
    FRAMEWORK = arguments['<framework_slug>']
    TEMPLATE_FOLDER = arguments['<template_folder>']
    OUTPUT_FOLDER = arguments['<output_folder>']

    repo_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..'))
    html_dir = os.path.join(OUTPUT_FOLDER, 'html')

    os.makedirs(html_dir)

    logger = logging.configure_logger()

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), API_TOKEN)

    headers, rows = find_suppliers_with_details(client, FRAMEWORK)

    render_html_for_successful_suppliers(rows, FRAMEWORK, TEMPLATE_FOLDER, html_dir)
    html_pages = os.listdir(html_dir)
    html_pages.remove('{}-signature-page.css'.format(FRAMEWORK))
    render_pdf_for_each_html_page(html_pages, html_dir, OUTPUT_FOLDER)
    shutil.rmtree(html_dir)
