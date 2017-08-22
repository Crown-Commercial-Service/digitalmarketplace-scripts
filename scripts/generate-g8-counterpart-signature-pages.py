#!/usr/bin/env python
"""

PREREQUISITE: You'll need wkhtmltopdf installed for this to work (http://wkhtmltopdf.org/)

Generate framework agreement counterpart signature pages from supplier "about you" information for suppliers
who applied to a framework.

This is a LEGACY script, retained for when we need to generate new G8 counterpart pages.
It will *only* work for framework_slug=g-cloud-8.

For any newer frameworks use generate-framework-agreement-counterpart-signature-pages.py instead.

Usage:
    scripts/generate-g8-counterpart-signature-pages.py <stage> <api_token> <framework_slug> <template_folder>
    <out_folder> [<supplier_id_file>]

Example:
    generate-g8-counterpart-signature-pages.py dev myToken g-cloud-8 \
    ../digitalmarketplace-agreements/documents/g-cloud pdf

"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.export_framework_applicant_details import get_csv_rows
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers.framework_helpers import find_suppliers_with_details_and_draft_service_counts
from dmscripts.helpers.supplier_data_helpers import get_supplier_ids_from_file
from dmscripts.generate_g8_agreement_signature_pages import render_html_for_suppliers_awaiting_countersignature, \
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

    supplier_id_file = arguments['<supplier_id_file>']
    supplier_ids = get_supplier_ids_from_file(supplier_id_file)

    records = find_suppliers_with_details_and_draft_service_counts(client, FRAMEWORK, supplier_ids)
    headers, rows = get_csv_rows(records, FRAMEWORK, count_statuses=("submitted",))
    render_html_for_suppliers_awaiting_countersignature(rows, FRAMEWORK, TEMPLATE_FOLDER, html_dir)

    html_pages = os.listdir(html_dir)
    html_pages.remove('{}-signature-page.css'.format(FRAMEWORK))
    html_pages.remove('{}-countersignature.png'.format(FRAMEWORK))
    render_pdf_for_each_html_page(html_pages, html_dir, OUTPUT_FOLDER)
    shutil.rmtree(html_dir)
