import io
from jinja2 import Environment, StrictUndefined

from dmutils.formats import nodaydateformat


def render_html(template_path, data=None):
    with io.open(template_path, encoding='UTF-8') as htmlfile:
        # Use StrictUndefined so that the template render throws an error if any required variables are not passed in.
        env = Environment(undefined=StrictUndefined)
        env.filters['nodaydateformat'] = nodaydateformat
        html = htmlfile.read()
        template = env.from_string(html)
        return template.render(data or {})
