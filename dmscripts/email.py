import io
from jinja2 import Template

from mandrill import Mandrill


def render_html(template_path, data=None):
    with io.open(template_path, encoding='UTF-8') as htmlfile:
        html = htmlfile.read()
        template = Template(html)
        return template.render(data or {})
