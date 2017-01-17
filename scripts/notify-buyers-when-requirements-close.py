#!/usr/bin/env python

"""Send email notifications to buyer users about closed requirements.

Usage:
    notify-buyers-when-requirements-close.py <stage> --api-token=<api_access_token>
                                                     --email-api-key=<email_api_key> [options]

    --date-closed=<date>  Notify about requirements that closed on the given date (date format: YYYY-MM-DD)
    --dry-run  List notifications that would be sent without sending the emails

"""

import sys

from docopt import docopt

sys.path.insert(0, '.')
from dmscripts.helpers.env import get_api_endpoint_from_stage
from dmscripts.notify_buyers_when_requirements_close import main


if __name__ == "__main__":
    arguments = docopt(__doc__)
    ok = main(
        data_api_url=get_api_endpoint_from_stage(arguments['<stage>'], 'api'),
        data_api_access_token=arguments['--api-token'],
        email_api_key=arguments['--email-api-key'],
        date_closed=arguments['--date-closed'],
        dry_run=arguments['--dry-run']
    )

    if not ok:
        sys.exit(1)
