import os
import io
import shutil
from jinja2 import Template


def render_html(data, template_path):
    with io.open(template_path, encoding='UTF-8') as htmlfile:
        html = htmlfile.read()
        template = Template(html)
        return template.render(data)

def save_page(html, supplier_id, output_dir):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    page_path  = os.path.join(output_dir, 'supplier-{}-signature-page.html'.format(supplier_id))
    with io.open(page_path, 'w+', encoding='UTF-8') as htmlfile:
        htmlfile.write(html)

def render_html_for_all_suppliers(rows, framework, template_dir, output_dir):
    template_path = os.path.join(template_dir, '{}-signature-page.html'.format(framework))
    template_css_path = os.path.join(template_dir, '{}-signature-page.css'.format(framework))
    for data in rows:
        data['appliedLots'] = filter(lambda lot: int(data[lot]) > 0, ['saas', 'paas', 'iaas', 'scs'])
        html = render_html(data, template_path)
        save_page(html, data['supplier_id'], output_dir)
    shutil.copyfile(template_css_path, os.path.join(output_dir, '{}-signature-page.css'.format(framework)))
