import os
import io
import shutil
import re
import subprocess

from datetime import datetime

from dmscripts.helpers.html_helpers import render_html
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging

logger = logging_helpers.configure_logger({'dmapiclient.base': logging.WARNING})


def save_page(html, supplier_id, output_dir, descriptive_filename_part):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    page_path = os.path.join(output_dir, '{}-{}.html'.format(supplier_id, descriptive_filename_part))
    with io.open(page_path, 'w+', encoding='UTF-8') as htmlfile:
        htmlfile.write(html)


def render_html_for_successful_suppliers(rows, framework, template_dir, output_dir):
    template_path = os.path.join(template_dir, 'framework-agreement-signature-page.html')
    template_css_path = os.path.join(template_dir, 'framework-agreement-signature-page.css')
    for data in rows:
        if data['pass_fail'] == 'fail':
            continue
        data['framework'] = framework
        data['awardedLots'] = [lot for lot in framework['frameworkAgreementDetails']['lotOrder'] if int(data[lot]) > 0]
        data['includeCountersignature'] = False
        html = render_html(template_path, data)
        save_page(html, data['supplier_id'], output_dir, "signature-page")
    shutil.copyfile(template_css_path, os.path.join(output_dir, 'framework-agreement-signature-page.css'))


def render_html_for_suppliers_awaiting_countersignature(rows, framework, template_dir, output_dir):
    template_path = os.path.join(template_dir, 'framework-agreement-signature-page.html')
    template_css_path = os.path.join(template_dir, 'framework-agreement-signature-page.css')
    countersignature_img_path = os.path.join(template_dir, 'framework-agreement-countersignature.png')
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
        data['awardedLots'] = [lot for lot in framework['lotOrder'] if int(data[lot]) > 0]
        data['countersigned_at'] = datetime.strptime(
            data['countersigned_at'], '%Y-%m-%dT%H:%M:%S.%fZ'
        ).strftime('%d %B %Y')
        data['includeCountersignature'] = True
        html = render_html(template_path, data)
        save_page(html, data['supplier_id'], output_dir, "agreement-countersignature")
    shutil.copyfile(template_css_path, os.path.join(output_dir, 'framework-agreement-signature-page.css'))
    shutil.copyfile(countersignature_img_path, os.path.join(output_dir, 'framework-agreement-countersignature.png'))


def render_pdf_for_each_html_page(html_pages, html_dir, pdf_dir):
    html_dir = os.path.abspath(html_dir)
    pdf_dir = os.path.abspath(pdf_dir)
    ok = True
    if not os.path.exists(pdf_dir):
        os.mkdir(pdf_dir)
    for index, html_page in enumerate(html_pages):
        html_path = os.path.join(html_dir, html_page)
        pdf_path = '{}'.format(re.sub(r'\.html$', '.pdf', html_path))
        pdf_path = '{}'.format(re.sub(html_dir, pdf_dir, pdf_path))
        exit_code = subprocess.call(['wkhtmltopdf', 'file://{}'.format(html_path), pdf_path])
        if exit_code > 0:
            logger.error("ERROR {} on {}".format(exit_code, html_page))
            ok = False
    return ok
