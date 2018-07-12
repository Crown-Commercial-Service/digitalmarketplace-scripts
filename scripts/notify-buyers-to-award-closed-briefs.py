#!/usr/bin/env python
"""Send email notifications to buyer users to remind them to award their closed requirements.

Usage:
    notify-buyers-to-award-closed-briefs.py <stage> <govuk_notify_api_key> <govuk_notify_template_id> [options]

Example:
    notify-buyers-to-award-closed-briefs.py local myNotifyToken myNotifyTemplateId --dry-run=True --buyer-ids=1

Options:
    -h, --help  Show this screen
    --date-closed=<date> Notify users of requirements closed on that date (date format: YYYY-MM-DD)
    --dry-run List notifications that would be sent without sending actual emails
    --buyer-ids List of buyer user IDs to be emailed
    --offset-days Days between brief closing and email being sent (defaults to 28)

"""

import sys

sys.path.insert(0, '.')
from docopt import docopt

from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.notify_buyers_to_award_closed_briefs import main


if __name__ == '__main__':
    arguments = docopt(__doc__)

    list_of_buyer_ids = []
    if arguments['--buyer-ids']:
        list_of_buyer_ids = list(map(int, arguments['--buyer-ids'].split(',')))
    if arguments['--offset-days']:
        offset_days = int(arguments['--offset-days'])
    else:
        offset_days = 28

    ok = main(
        data_api_url=get_api_endpoint_from_stage(arguments['<stage>'], 'api'),
        data_api_access_token=get_auth_token('api', arguments['<stage>']),
        notify_api_key=arguments['<govuk_notify_api_key>'],
        notify_template_id=arguments['<govuk_notify_template_id>'],
        date_closed=arguments['--date-closed'],
        dry_run=arguments['--dry-run'],
        user_id_list=list_of_buyer_ids,
        offset_days=offset_days
    )

    if not ok:
        sys.exit(1)
