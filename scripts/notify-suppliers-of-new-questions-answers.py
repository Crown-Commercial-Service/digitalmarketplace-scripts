#!/usr/bin/env python

"""Send email notifications to supplier users when a question has been answered

Usage:
    notify-suppliers-of-new-questions-answers.py <stage> --api-token=<api_access_token>
                                                     --email-api-key=<email_api_key> [options]

    --number-of-days=<days>  Length of window for recent questions/answers
    --dry-run  List notifications that would be sent without sending the emails
"""

import sys

from docopt import docopt

sys.path.insert(0, '.')
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.notify_suppliers_of_new_questions_answers import main


if __name__ == "__main__":
    arguments = docopt(__doc__)
    ok = main(
        data_api_url=get_api_endpoint_from_stage(arguments['<stage>'], 'api'),
        data_api_token=arguments['--api-token'],
        email_api_key=arguments['--email-api-key'],
        stage=arguments['<stage>'],
        number_of_days=arguments['--number-of-days'],
        dry_run=arguments['--dry-run']
    )

    if not ok:
        sys.exit(1)
