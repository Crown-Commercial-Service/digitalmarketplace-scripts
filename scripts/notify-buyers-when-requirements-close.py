#!/usr/bin/env python

"""Send email notifications to buyer users about closed requirements.

Usage:
    notify-buyers-when-requirements-close.py <stage> --email-api-key=<email_api_key> [options]

    --date-closed=<date>  Notify about requirements that closed on the given date (date format: YYYY-MM-DD)
    --dry-run  List notifications that would be sent without sending the emails

"""

import sys

from docopt import docopt

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.notify_buyers_when_requirements_close import main
from dmutils.env_helpers import get_api_endpoint_from_stage


if __name__ == "__main__":
    arguments = docopt(__doc__)
    ok = main(
        data_api_url=get_api_endpoint_from_stage(arguments['<stage>'], 'api'),
        data_api_access_token=get_auth_token('api', arguments['<stage>']),
        email_api_key=arguments['--email-api-key'],
        stage=arguments['<stage>'],
        date_closed=arguments['--date-closed'],
        dry_run=arguments['--dry-run']
    )

    if not ok:
        sys.exit(1)
