#!/usr/bin/env python
"""

PREREQUISITE: You'll need wkhtmltopdf installed for this to work (http://wkhtmltopdf.org/)

Generate framework agreement counterpart signature pages from supplier "about you" information for suppliers
who applied to a framework.

Currently will only work for framework_slug=g-cloud-8.

To add support for future frameworks we will will need to add to the LOTS and DECLARATION_FIELDS in
dmscripts/export_framework_applicant_details.py

Usage:
    scripts/generate-counterpart-signature-pages.py <stage> <api_token> <framework_slug> <template_folder> <out_folder>

Example:
    generate-counterpart-signature-pages.py dev myToken g-cloud-8 ../digitalmarketplace-agreements/documents/g-cloud pdf

"""
import sys
import os
import shutil
import tempfile

sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.env import get_api_endpoint_from_stage
from dmscripts.export_framework_applicant_details import find_suppliers_with_details
from dmscripts.generate_agreement_signature_pages import render_html_for_suppliers_awaiting_countersignature, \
    render_pdf_for_each_html_page
from dmapiclient import DataAPIClient


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    API_TOKEN = arguments['<api_token>']
    FRAMEWORK = arguments['<framework_slug>']
    TEMPLATE_FOLDER = arguments['<template_folder>']
    OUTPUT_FOLDER = arguments['<out_folder>']

    html_dir = tempfile.mkdtemp()

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), API_TOKEN)

    headers, rows = find_suppliers_with_details(client, FRAMEWORK)

    render_html_for_suppliers_awaiting_countersignature(rows, FRAMEWORK, TEMPLATE_FOLDER, html_dir)

    html_pages = os.listdir(html_dir)
    html_pages.remove('{}-signature-page.css'.format(FRAMEWORK))
    html_pages.remove('{}-countersignature.png'.format(FRAMEWORK))
    render_pdf_for_each_html_page(html_pages, html_dir, OUTPUT_FOLDER)
    shutil.rmtree(html_dir)
