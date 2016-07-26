import os
import io
import shutil
import re
import subprocess
from jinja2 import Template


def render_html(data, template_path):
    with io.open(template_path, encoding='UTF-8') as htmlfile:
        html = htmlfile.read()
        template = Template(html)
        return template.render(data)


def save_page(html, supplier_id, output_dir):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    page_path = os.path.join(output_dir, '{}-signature-page.html'.format(supplier_id))
    with io.open(page_path, 'w+', encoding='UTF-8') as htmlfile:
        htmlfile.write(html)


def render_html_for_successful_suppliers(rows, framework, template_dir, output_dir):
    template_path = os.path.join(template_dir, '{}-signature-page.html'.format(framework))
    template_css_path = os.path.join(template_dir, '{}-signature-page.css'.format(framework))
    for data in rows:
        if data['on_framework'] is False:
            continue
        data['appliedLots'] = filter(lambda lot: int(data[lot]) > 0, ['saas', 'paas', 'iaas', 'scs'])
        html = render_html(data, template_path)
        save_page(html, data['supplier_id'], output_dir)
    shutil.copyfile(template_css_path, os.path.join(output_dir, '{}-signature-page.css'.format(framework)))


def render_pdf_for_each_html_page(html_pages, html_dir, pdf_dir):
    html_dir = os.path.abspath(html_dir)
    pdf_dir = os.path.abspath(pdf_dir)
    if not os.path.exists(pdf_dir):
        os.mkdir(pdf_dir)
    for index, html_page in enumerate(html_pages):
        html_path = os.path.join(html_dir, html_page)
        pdf_path = '{}'.format(re.sub(r'\.html$', '.pdf', html_path))
        pdf_path = '{}'.format(re.sub(html_dir, pdf_dir, pdf_path))
        exit_code = subprocess.call(['wkhtmltopdf', 'file://{}'.format(html_path), pdf_path])
        if exit_code > 0:
            print("ERROR: {} on {}".format(exit_code, html_page))
