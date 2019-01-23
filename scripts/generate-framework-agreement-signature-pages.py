#!/usr/bin/env python
"""
Generate framework agreement signature pages from supplier "about you"
information for suppliers who successfully applied to a framework.

Usage:
    scripts/generate-framework-agreement-signature-pages.py [-v...] [options]
        <stage> <framework> <output_dir> <agreements_repo>
        [--supplier-id=<id>... | --supplier-ids-from=<file>]
    scripts/generate-framework-agreement-signature-pages.py (-h | --help)

Options:
    <stage>                     Environment to run script against.
    <framework>                 Slug of framework to generate agreements for.
    <output_dir>                Path to folder where script will save output.
    <agreements_repo>           Path to folder containing framework templates.

    --supplier-id=<id>          ID of supplier to generate agreement page for.
    --supplier-ids-from=<file>  Path to file containing supplier IDs, one per line.

    -h, --help                  Show this help message

    -n, --dry-run               Run script without generating files.
    -t <n>, --threads=<n>       Number of threads to use, if not supplied the
                                script will be run without threading.
    -v, --verbose               Show debug log messages.

    If neither `--supplier-ids-from` or `--supplier-id` are provided then
    framework agreements will be generated for all valid suppliers.

PREREQUISITE: You'll need wkhtmltopdf installed for this to work
(http://wkhtmltopdf.org/)

As well as calling out to the Digital Marketplace api, this script uses the
online countries register.

PDF signature pages are generated for all suppliers that have a framework
interest and at least one completed draft service.
"""
from multiprocessing.pool import ThreadPool
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, ".")

from docopt import docopt

from dmscripts.export_framework_applicant_details import get_csv_rows
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.framework_helpers import (
    find_suppliers_with_details_and_draft_service_counts
)
from dmscripts.helpers.logging_helpers import (
    configure_logger,
    logging,
)
from dmscripts.helpers.supplier_data_helpers import get_supplier_ids_from_file

from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage

from dmscripts.generate_framework_agreement_signature_pages import (
    render_html_for_successful_suppliers,
    render_pdf_for_each_html_page,
)


if __name__ == "__main__":
    args = docopt(__doc__)

    if args["--supplier-ids-from"]:
        supplier_ids = get_supplier_ids_from_file(args["--supplier-ids-from"])
    elif args["--supplier-id"]:
        try:
            supplier_ids = tuple(map(int, args["--supplier-id"]))
        except ValueError:
            raise TypeError("argument to --supplier-id should be an integer")
    else:
        supplier_ids = None

    stage = args["<stage>"]
    framework_slug = args["<framework>"]
    agreements_repo = pathlib.Path(args["<agreements_repo>"])
    agreements_dir = agreements_repo / "documents" / framework_slug
    output_dir = pathlib.Path(args["<output_dir>"])

    dry_run = args["--dry-run"]
    verbose = args["--verbose"]
    if args["--threads"]:
        map_impl = ThreadPool(int(args["--threads"])).imap
    else:
        map_impl = map

    logger = configure_logger({
        "dmapiclient.base": logging.WARNING,
        "framework_helpers": logging.DEBUG if verbose >= 2 else logging.WARNING,
        "script": logging.DEBUG if verbose else logging.INFO,
    })

    logger.debug(f"connecting to api on {stage}")
    client = DataAPIClient(
        get_api_endpoint_from_stage(args["<stage>"]),
        get_auth_token("api", args["<stage>"]),
    )

    logger.debug(f"fetching lots for framework '{framework_slug}'")
    framework = client.get_framework(framework_slug)["frameworks"]
    framework_lot_slugs = tuple([lot["slug"] for lot in client.get_framework(framework_slug)["frameworks"]["lots"]])

    # get supplier details (returns a lazy generator)
    logger.debug(f"fetching records for {len(supplier_ids) if supplier_ids else 'all'} suppliers")
    records = find_suppliers_with_details_and_draft_service_counts(
        client,
        framework_slug,
        supplier_ids,
        map_impl=map_impl,
    )
    # we reuse code from another script to filter and flatten our supplier details
    _, rows = get_csv_rows(
        records,
        framework_slug,
        framework_lot_slugs,
        count_statuses=("submitted",),
        dry_run=dry_run,
    )

    # create a temporary directory for the HTML files
    with tempfile.TemporaryDirectory() as html_dir:
        # create signature pages in HTML using Jinja templates from agreements repo
        logger.debug(f"generating HTML signature pages")
        render_html_for_successful_suppliers(
            rows, framework, agreements_dir, html_dir, dry_run)

        # convert HTML to PDF (this uses wkhtmltopdf under-the-hood)
        logger.debug(f"generating PDF signature pages from HTML")
        html_pages = os.listdir(html_dir)
        html_pages.remove("framework-agreement-signature-page.css")
        render_pdf_for_each_html_page(html_pages, html_dir, output_dir)
