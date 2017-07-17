#!/usr/bin/env python
"""
Send email notifications to supplier users when a question has been answered

Usage: notify-suppliers-of-new-questions-answers.py <stage> <api_token> <mandrill_api_key> [options]

Options:
    --dry-run                               List notifications that would be sent without sending the emails
    --exclude-supplier-ids=EXCLUDE-SUPPLIERS   Comma separated list of suppliers IDs to be excluded. This is incase the
                                            script fails halfway and we need to resume it without sending emails twice
                                            to any supplier

Examples:
    ./scripts/notify-suppliers-of-new-questions-answers.py preview myToken
        mandrillToken --dry-run --exclude-supplier-ids=2,3,4
"""

import sys

from docopt import docopt

sys.path.insert(0, '.')
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.notify_suppliers_of_new_questions_answers import main


if __name__ == "__main__":
    arguments = docopt(__doc__)

    list_of_excluded_supplier_ids = []
    if arguments['--exclude-supplier-ids']:
        list_of_excluded_supplier_ids = map(int, arguments['--exclude-supplier-ids'].split(','))

    ok = main(
        data_api_url=get_api_endpoint_from_stage(arguments['<stage>'], 'api'),
        data_api_token=arguments['<api_token>'],
        email_api_key=arguments['<mandrill_api_key>'],
        stage=arguments['<stage>'],
        dry_run=arguments['--dry-run'],
        exclude_supplier_ids=list_of_excluded_supplier_ids
    )

    if not ok:
        sys.exit(1)
