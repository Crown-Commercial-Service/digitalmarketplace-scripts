import io
from jinja2 import Template

from mandrill import Mandrill


def render_html(template_path, data=None):
    with io.open(template_path, encoding='UTF-8') as htmlfile:
        html = htmlfile.read()
        template = Template(html)
        return template.render(data or {})


def get_sent_emails(mandrill_api_key, tags, date_from=None):
    mandrill_client = Mandrill(mandrill_api_key)

    return mandrill_client.messages.search(tags=tags, date_from=date_from, limit=1000)
