import os
import io
import shutil
import subprocess
from pathlib import Path

from datetime import datetime
from typing import NamedTuple

from PyPDF2 import PdfFileMerger

from dmscripts.helpers.html_helpers import render_html
from dmscripts.helpers.logging_helpers import get_logger
from dmscripts.helpers.framework_helpers import (
    find_suppliers_with_details_and_draft_service_counts,
    framework_supports_e_signature
)
from dmscripts.export_framework_applicant_details import get_csv_rows

logger = get_logger()


def find_suppliers(client, framework, supplier_ids=None, map_impl=map, dry_run=False):
    """Return supplier details for suppliers with framework interest

    :param client: data api client
    :type client: dmapiclient.DataAPIClient
    :param dict framework: framework
    :param supplier_ids: list of supplier IDs to limit return to
    :type supplier_ids: Optional[List[Union[str, int]]]
    """
    # get supplier details (returns a lazy generator)
    logger.debug(f"fetching records for {len(supplier_ids) if supplier_ids else 'all'} suppliers")
    records = find_suppliers_with_details_and_draft_service_counts(
        client,
        framework["slug"],
        supplier_ids,
        map_impl=map_impl,
    )
    # we reuse code from another script to filter and flatten our supplier details
    _, rows = get_csv_rows(
        records,
        framework["slug"],
        framework_lot_slugs=tuple([lot["slug"] for lot in framework["lots"]]),
        count_statuses=("submitted",),
        dry_run=dry_run,
        include_central_supplier_details=True
    )
    return rows


def save_page(html, supplier_id, output_dir, descriptive_filename_part):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    page_path = os.path.join(output_dir, '{}-{}.html'.format(supplier_id, descriptive_filename_part))
    with io.open(page_path, 'w+', encoding='UTF-8') as htmlfile:
        htmlfile.write(html)
    return page_path


def render_html_for_successful_suppliers(rows, framework, template_dir, output_dir, dry_run=False):
    template_path = os.path.join(template_dir, 'framework-agreement-signature-page.html')
    template_css_path = os.path.join(template_dir, 'framework-agreement-signature-page.css')

    for data in rows:
        if data['pass_fail'] in ('fail', 'discretionary'):
            logger.info(f"skipping supplier {data['supplier_id']} due to pass_fail=='{data['pass_fail']}'")
            continue

        logger.info(f"generating framework agreement page for successful supplier {data['supplier_id']}")

        data['framework'] = framework
        data['awardedLots'] = [lot for lot in framework['frameworkAgreementDetails']['lotOrder'] if int(data[lot]) > 0]
        data['includeCountersignature'] = False

        if dry_run:
            continue

        html = render_html(template_path, data)
        save_page(html, data['supplier_id'], output_dir, "signature-page")

    shutil.copyfile(template_css_path, os.path.join(output_dir, 'framework-agreement-signature-page.css'))


def render_html_for_suppliers_awaiting_countersignature(rows, framework, template_dir, output_dir, *, dry_run=False):
    output_dir = Path(output_dir).resolve()
    html_pages = []
    static_files = []

    if framework_supports_e_signature(framework):
        if framework['slug'] == 'g-cloud-12':
            html_pages.append(Path(template_dir, 'framework-agreement-cover-page.html'))
            html_pages.append(Path(template_dir, 'framework-agreement-appointment-page-1.html'))
            html_pages.append(Path(template_dir, 'framework-agreement-appointment-page-2.html'))
            static_files.append(Path(template_dir, 'ccs_logo.png'))
            static_files.append(Path(template_dir, 'framework-agreement-appointment-page.css'))
            static_files.append(Path(template_dir, 'framework-agreement-cover-page.css'))
            static_files.append(Path(template_dir, 'framework-agreement-toc.pdf'))
            static_files.append(Path(template_dir, 'framework-agreement-boilerplate.pdf'))
        elif framework['slug'] == 'digital-outcomes-and-specialists-5':
            html_pages.append(Path(template_dir, 'framework-award-section-1.html'))
            html_pages.append(Path(template_dir, 'framework-award-section-2.html'))
            static_files.append(Path(template_dir, 'framework-award.css'))
            static_files.append(Path(template_dir, 'cover-page.pdf'))
            static_files.append(Path(template_dir, 'boilerplate.pdf'))
        else:
            raise ValueError('Unknown e-signature framework')
    else:
        # Only non e-signature document includes countersignature graphic
        html_pages.append(Path(template_dir, 'framework-agreement-signature-page.html'))
        static_files.append(Path(template_dir, 'framework-agreement-countersignature.png'))
        static_files.append(Path(template_dir, 'framework-agreement-signature-page.css'))

    for data in rows:
        if data['pass_fail'] == 'fail' or data['countersigned_path'] or not data['countersigned_at']:
            logger.info("SKIPPING {}: pass_fail={} countersigned_at={} countersigned_path={}".format(
                data['supplier_id'],
                data['pass_fail'],
                data['countersigned_at'],
                data['countersigned_path'])
            )
            continue
        data['framework'] = framework
        data['awardedLots'] = [lot for lot in framework['frameworkAgreementDetails']['lotOrder'] if int(data[lot]) > 0]
        data['countersigned_at'] = datetime.strptime(
            data['countersigned_at'], '%Y-%m-%dT%H:%M:%S.%fZ'
        ).strftime('%d %B %Y')
        if data['signed_agreement_returned_at']:
            data['signed_agreement_returned_at'] = datetime.strptime(
                data['signed_agreement_returned_at'], '%Y-%m-%dT%H:%M:%S.%fZ'
            ).strftime('%d %B %Y')
        data['includeCountersignature'] = True

        # TODO: the template should get these details from the agreement object rather than the framework object
        # but currently the agreement object isn't in the data dict so for now we need to do this
        # TODO: instead of this, add a watermark to the PDF
        if dry_run:
            framework["frameworkAgreementDetails"]["countersignerName"] = "------DRAFT------"
            framework["frameworkAgreementDetails"]["countersignerRole"] = "------DRAFT------"

        logger.info(f"generating coutersigned agreement PDF for {data['supplier_id']}")

        html_dir = output_dir / str(data['supplier_id'])
        output_pages = []
        for html_page in html_pages:
            html = render_html(str(html_page), data)
            page_path = save_page(html, data['supplier_id'], html_dir, html_page.stem)
            output_pages.append(Path(page_path).resolve())

        for static_file in static_files:
            Path(html_dir, static_file.name).symlink_to(static_file.resolve())

        yield html_dir, output_pages


def render_pdf_for_each_html_page(html_pages, html_dir, pdf_dir, framework_slug):
    html_dir = Path(html_dir).resolve()
    pdf_dir = Path(pdf_dir).resolve()

    ok = True

    if not os.path.exists(pdf_dir):
        os.mkdir(pdf_dir)

    if len(html_pages) > 1:
        for index, html_path in enumerate(html_pages):
            pdf_path = html_dir / (html_path.stem + ".pdf")
            # Insert page number for dynamically generated pages
            if framework_slug == "g-cloud-12":
                page_numbers = {0: "1",
                                1: "3",
                                2: "4"}
            elif framework_slug == "digital-outcomes-and-specialists-5":
                page_numbers = {0: "2", 1: "9"}
            else:
                raise ValueError(f"Unsupported e-signatures framework {framework_slug}")

            proc = subprocess.run(
                [
                    'wkhtmltopdf',
                    '--log-level', 'warn',
                    '--enable-local-file-access',
                    '--footer-right',
                    page_numbers.get(index, ""),
                    '--margin-top',
                    '25mm',
                    '--margin-bottom',
                    '20mm',
                    '--margin-right',
                    '20mm',
                    'file://{}'.format(html_path),
                    pdf_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
            if proc.returncode > 0:
                logger.error(f"ERROR {proc.returncode} on {html_path}: {proc.stdout}")
                ok = False
            elif proc.stdout:
                logger.warn(proc.stdout)
        merge_e_signature_docs(html_dir, pdf_dir, framework_slug)
    else:
        html_path = html_pages[0]
        pdf_path = pdf_dir / (html_path.stem + ".pdf")
        exit_code = subprocess.call(['wkhtmltopdf', 'file://{}'.format(html_path), pdf_path])
        if exit_code > 0:
            logger.error("ERROR {} on {}".format(exit_code, html_path))
            ok = False

    return ok


def merge_e_signature_docs(input_dir, output_dir, framework_slug):
    supplier_id = input_dir.name

    class PdfWithOffset(NamedTuple):
        filename: str
        position_offset: int = 0

    if framework_slug == "g-cloud-12":
        pdf_list = [
            PdfWithOffset(input_dir / f"{supplier_id}-framework-agreement-cover-page.pdf"),
            PdfWithOffset(input_dir / "framework-agreement-toc.pdf"),
            PdfWithOffset(input_dir / f"{supplier_id}-framework-agreement-appointment-page-1.pdf"),
            PdfWithOffset(input_dir / f"{supplier_id}-framework-agreement-appointment-page-2.pdf"),
            PdfWithOffset(input_dir / "framework-agreement-boilerplate.pdf"),
        ]
    elif framework_slug == "digital-outcomes-and-specialists-5":
        pdf_list = [
            PdfWithOffset(input_dir / "cover-page.pdf"),
            PdfWithOffset(input_dir / f"{supplier_id}-framework-award-section-1.pdf"),
            PdfWithOffset(input_dir / "boilerplate.pdf"),
            PdfWithOffset(input_dir / f"{supplier_id}-framework-award-section-2.pdf", 5)
        ]
    else:
        raise ValueError(f"Unsupported e-signature framework {framework_slug}")

    assert all(pdf.filename.exists() for pdf in pdf_list)

    pdf_file_merger = PdfFileMerger()
    for index, PdfWithOffset in enumerate(pdf_list):
        pdf_file_merger.merge(position=index + PdfWithOffset.position_offset,
                              fileobj=str(PdfWithOffset.filename.resolve()),
                              import_bookmarks=False)
    pdf_file_merger.write(f"{output_dir}/{supplier_id}-framework-agreement-signature-page.pdf")
