#!/usr/bin/env python3
"""
Get all the emails from mailchimp for people who've asked to be notified about new framework iterations.

Usage:
    /export-mailchimp-coming-emails.py <stage> <since> [--verbose]

Parameters:
    <stage>  Stage to target
    <since>  The date when the previous framework closed for applications. In ISO format: YYYY-MM-DD
"""
import csv
import logging
import sys

from dateutil.parser import isoparse
from dmutils.email.dm_mailchimp import DMMailChimpClient
from docopt import docopt

sys.path.insert(0, ".")

from dmscripts.helpers import logging_helpers
from dmscripts.helpers.auth_helpers import get_mailchimp_credentials

TEST_AUDIENCE_ID = "18fb1fa411"  # PREVIEW OPEN_FRAMEWORK_NOTIFICATION_MAILING_LIST
PRODUCTION_AUDIENCE_ID = "7534b3e89a"  # Digital Marketplace - open for applications


def output_emails_as_csv(email_addresses):
    writer = csv.writer(sys.stdout, delimiter=",", quotechar='"')
    writer.writerow(["email address"])
    for email_address in email_addresses:
        writer.writerow([email_address])


if __name__ == "__main__":
    arguments = docopt(__doc__)

    logger = logging_helpers.configure_logger(
        {"dmapiclient": logging.INFO}
        if arguments["--verbose"]
        else {"dmapiclient": logging.WARN}
    )

    stage = arguments["<stage>"]
    (username, api_key) = get_mailchimp_credentials(stage)
    dm_mailchimp_client = DMMailChimpClient(
        username,
        api_key,
        logger,
    )

    audience_id = PRODUCTION_AUDIENCE_ID if stage == "production" else TEST_AUDIENCE_ID
    since = isoparse(arguments["<since>"])
    email_addresses = dm_mailchimp_client.get_email_addresses_from_list(
        audience_id,
        status="subscribed",
        since_timestamp_opt=since.isoformat(),
    )
    output_emails_as_csv(email_addresses)
