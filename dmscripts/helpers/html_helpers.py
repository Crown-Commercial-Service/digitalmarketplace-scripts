from datetime import datetime
import io
from jinja2 import Environment, StrictUndefined

from dmutils.formats import nodaydateformat, DATETIME_FORMAT


def dos2_date_format(datetime_string_utc):
    """Needed just for DOS2 agreements. Remove this when DOS2 expires."""
    dt = datetime.strptime(datetime_string_utc, DATETIME_FORMAT)
    return dt.strftime('%-d/%m/%Y')


def render_html(template_path, data=None):
    with io.open(template_path, encoding='UTF-8') as htmlfile:
        # Use StrictUndefined so that the template render throws an error if any required variables are not passed in.
        env = Environment(undefined=StrictUndefined)
        env.filters['nodaydateformat'] = nodaydateformat
        env.filters['dos2_date_format'] = dos2_date_format
        html = htmlfile.read()
        template = env.from_string(html)
        return template.render(data or {})
