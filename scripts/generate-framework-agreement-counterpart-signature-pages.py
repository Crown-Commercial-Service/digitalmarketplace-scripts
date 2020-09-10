#!/usr/bin/env python3
"""

PREREQUISITE: You'll need wkhtmltopdf installed for this to work (http://wkhtmltopdf.org/). The `default.nix` in this
repo can provide this dependency.

Generate framework agreement counterpart signature pages from supplier "about you" information for suppliers
who successfully applied to a framework and whose signed agreements have been approved by CCS.

The 'frameworkAgreementDetails' JSON object from the API should look something like this:
{
    "contractNoticeNumber": "2016/S 217-395765",
    "frameworkAgreementVersion": "RM1043iv",
    "frameworkExtensionLength": "12 months",
    "frameworkRefDate": "16-01-2017",
    "frameworkURL": "https://www.gov.uk/government/publications/digital-outcomes-and-specialists-2-framework-agreement",
    "lotDescriptions": {
      "digital-outcomes": "Lot 1: digital outcomes",
      "digital-specialists": "Lot 2: digital specialists",
      "user-research-participants": "Lot 4: user research participants",
      "user-research-studios": "Lot 3: user research studios"
    },
    "lotOrder": [
      "digital-outcomes",
      "digital-specialists",
      "user-research-studios",
      "user-research-participants"
    ],
    "pageTotal": 45,
    "signaturePageNumber": 3
}

`countersignature_path` is a path pointing at an image file of a signature to use when 'signing' the agreement,
which should be at `digitalmarketplace-credentials/signatures/<name>.png`

Usage:
    scripts/generate-framework-agreement-counterpart-signature-pages.py [options]
        [--supplier-id=<id> ... | --supplier-ids-from=<file>]
        <stage> <framework_slug> <path_to_agreements_repo> <output_folder>

Options:
    <stage>                     Environment to run script against.
    <framework>                 Framework slug.
    <path_to_agreements_repo>   Path to directory with agreements repo.
    <output_folder>             Path to output PDFs.

    --supplier-id=<id>          ID(s) of supplier(s) to email.
    --supplier-ids-from=<file>  Path to file containing supplier ID(s), one per line.

    -h, --help                  Show this screen
    -v, --verbose               Log verbosely
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.export_framework_applicant_details import get_csv_rows
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.framework_helpers import find_suppliers_with_details_and_draft_service_counts, \
    framework_supports_e_signature
from dmscripts.helpers.logging_helpers import configure_logger
from dmscripts.helpers.supplier_data_helpers import get_supplier_ids_from_args
from dmscripts.generate_framework_agreement_signature_pages import (
    render_html_for_suppliers_awaiting_countersignature, render_pdf_for_each_html_page
)
from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage

AUTOMATED_COUNTERSIGNING_USER_ID = 64041

if __name__ == '__main__':
    args = docopt(__doc__)

    if args["--verbose"]:
        configure_logger({
            "dmapiclient": "INFO",
            "dmscripts.generate_framework_agreement_signature_pages": "DEBUG",
            "framework_helpers": "DEBUG",
        })
    else:
        configure_logger({
            "dmapiclient": "WARN",
            "dmscripts.generate_framework_agreement_signature_pages": "INFO",
            "framework_helpers": "INFO",
        })

    framework_slug = args['<framework_slug>']
    client = DataAPIClient(get_api_endpoint_from_stage(args['<stage>']), get_auth_token('api', args['<stage>']))
    framework = client.get_framework(framework_slug)['frameworks']
    framework_lot_slugs = tuple([lot['slug'] for lot in client.get_framework(framework_slug)['frameworks']['lots']])

    supplier_ids = get_supplier_ids_from_args(args)
    html_dir = tempfile.mkdtemp()

    records = find_suppliers_with_details_and_draft_service_counts(client, framework_slug, supplier_ids)
    records = list(records)
    for record in records:
        if framework_supports_e_signature(record['frameworkSlug']) and \
                (client.get_framework_agreement(record['agreementId'])
                 ['agreement']['status'] == 'signed'):
            # E-signatures are automatically approved.
            client.approve_agreement_for_countersignature(record['agreementId'],
                                                          "automated countersignature script",
                                                          AUTOMATED_COUNTERSIGNING_USER_ID)

    headers, rows = get_csv_rows(
        records, framework_slug, framework_lot_slugs, count_statuses=("submitted",),
        include_central_supplier_details=True
    )

    html_to_render = render_html_for_suppliers_awaiting_countersignature(
        rows, framework, os.path.join(args['<path_to_agreements_repo>'], 'documents', framework['slug']), html_dir
    )

    ok = True
    for html_dir, html_pages in html_to_render:
        ok = render_pdf_for_each_html_page(html_pages, html_dir, args['<output_folder>'],
                                           framework_slug=framework['slug']) and ok

    if ok:
        shutil.rmtree(html_dir)
    if not ok:
        sys.exit(1)
