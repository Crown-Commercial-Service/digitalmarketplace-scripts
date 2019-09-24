#!/usr/bin/env python3

"""
Default behaviour is to fetch any briefs (regardless of framework/lot) published in the last N days.

The script groups briefs by framework/lot, and for each combination, looks up the Mailchimp list ID, and creates &
sends a new campaign.
- If a framework_override is supplied, just find briefs for that framework
- If a lot_override is supplied, just find briefs for that lot
- If a list_id_override is supplied, only send emails to that list ID regardless of lot/framework

For testing purposes, you can override the list ID so you can send it to yourself only (use the sandbox list ID
"096e52cebb").

For most of the year, there should only be one framework iteration with live briefs. However during the transition
period between DOS framework iterations, we need to support both iterations.

For example, on the second day of DOS4, any DOS3 briefs created the first day (before the go-live switchover) will
still need to be emailed to DOS3 suppliers, as well as the usual DOS4 briefs sent to DOS4 suppliers.

Number of days tells the script for how many days before current date it should include in its search for briefs
    example:  if you run this script on a Wednesday and set number of days=1,
                then it will only include briefs from Tuesday (preceding day).
    example2: if you run it on Wednesday and set number of days=3,
                then it will include all briefs published on Sunday, Monday and Tuesday.
By default, the script will send 3 days of briefs on a Monday (briefs from Fri, Sat, Sun) and 1 day on all other
days. This can be overriden as described above.

If you only need to send opportunities for one lot rather than all of them, you can also do this via the command
line. Note, this may come in useful if the script was to fail halfway and you wish to continue from the lot which
failed.

Usage:
    send-dos-opportunities-email.py <stage> <mailchimp_username> <mailchimp_api_key> <framework_slug>
        [--number_of_days=<number_of_days>] [--list_id=<list_id>] [--lot_slug=<lot_slug>]

Example:
    send-dos-opportunities-email.py
        preview my.username@example.gov.uk myMailchimpKey digital-outcomes-and-specialists-3
        --number_of_days=3 --list_id=096e52cebb --lot_slug=digital-outcomes
"""

import sys

from datetime import date

from docopt import docopt
from dmapiclient import DataAPIClient

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.send_dos_opportunities_email import main
from dmscripts.helpers import logging_helpers
from dmutils.email.dm_mailchimp import DMMailChimpClient
from dmutils.env_helpers import get_api_endpoint_from_stage


logger = logging_helpers.configure_logger()


MAILCHIMP_LIST_IDS = {
    'digital-outcomes-and-specialists-2': {
        'digital-specialists': "30ba9fdf39",
        'digital-outcomes': "97952fee38",
        'user-research-participants': "e6b93a3bce",
    },
    'digital-outcomes-and-specialists-3': {
        'digital-specialists': "bee802d641",
        'digital-outcomes': "5c92c78a78",
        'user-research-participants': "34ebe0bffa",
    },
    'digital-outcomes-and-specialists-4': {
        'digital-specialists': "29d06d5201",
        'digital-outcomes': "4360debc5a",
        'user-research-participants': "2538f8a0f1",
    },
}

SANDBOX_LIST_ID = "096e52cebb"


if __name__ == "__main__":
    arguments = docopt(__doc__)

    stage = arguments['<stage>']
    number_of_days = arguments.get("--number_of_days")
    list_id = arguments.get("--list_id")
    lot_slug = arguments.get("--lot_slug")

    framework_slug = arguments['<framework_slug>']

    # Override number of days
    if number_of_days:
        number_of_days = int(number_of_days)
    else:
        day_of_week = date.today().weekday()
        if day_of_week == 0:
            number_of_days = 3  # If Monday, then 3 days of briefs
        else:
            number_of_days = 1

    # Override list IDs if supplied by script arg, or if environment is not production
    if list_id:
        logger.info("Sending to list ID {}".format(list_id))
        list_id_override = list_id
    elif stage != "production":
        logger.info("The environment is not production. Emails will be sent to test list.")
        list_id_override = SANDBOX_LIST_ID
    else:
        list_id_override = None

    api_url = get_api_endpoint_from_stage(stage)
    data_api_client = DataAPIClient(api_url, get_auth_token('api', stage))

    dm_mailchimp_client = DMMailChimpClient(arguments['<mailchimp_username>'], arguments['<mailchimp_api_key>'], logger)

    ok = main(

        data_api_client,
        dm_mailchimp_client,
        number_of_days,
        framework_override=framework_slug,
        list_id_override=list_id,
        lot_slug_override=lot_slug
    )
    if not ok:
        sys.exit(1)
