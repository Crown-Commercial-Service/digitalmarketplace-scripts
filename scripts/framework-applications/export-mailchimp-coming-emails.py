#!/usr/bin/env python3
"""
Get all the emails from mailchimp for people who've asked to be notified about new framework iterations.

Usage:
    /export-mailchimp-coming-emails.py <stage> <previous_framework> [--verbose]

Parameters:
    <stage>               Stage to target
    <previous_framework>  The previous framework in this family
"""
import csv
import logging
import sys

from dateutil.parser import isoparse
from dmapiclient import DataAPIClient
from dmutils.email.dm_mailchimp import DMMailChimpClient
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt

sys.path.insert(0, ".")

from dmscripts.helpers import logging_helpers
from dmscripts.helpers.auth_helpers import get_mailchimp_credentials, get_auth_token

TEST_AUDIENCE_ID = "18fb1fa411"  # PREVIEW OPEN_FRAMEWORK_NOTIFICATION_MAILING_LIST
PRODUCTION_AUDIENCE_ID = "7534b3e89a"  # Digital Marketplace - open for applications


def output_emails_as_csv(email_addresses):
    writer = csv.writer(sys.stdout, delimiter=",", quotechar='"')
    writer.writerow(["email address"])
    for email_address in email_addresses:
        writer.writerow([email_address])


def get_date_framework_closed(stage, framework_slug):
    data_api_client = DataAPIClient(
        get_api_endpoint_from_stage(stage), get_auth_token("api", stage)
    )
    framework = data_api_client.get_framework(framework_slug)["frameworks"]
    return isoparse(framework["applicationsCloseAtUTC"])


def get_email_addresses_from_mailchimp(stage, previous_framework_slug):
    (username, api_key) = get_mailchimp_credentials(stage)
    dm_mailchimp_client = DMMailChimpClient(
        username,
        api_key,
        logger,
    )

    audience_id = PRODUCTION_AUDIENCE_ID if stage == "production" else TEST_AUDIENCE_ID
    return dm_mailchimp_client.get_email_addresses_from_list(
        audience_id,
        status="subscribed",
        # Exclude people who've already been contacted about previous frameworks. We assume that they would have applied
        # to the previous framework if they were interested.
        since_timestamp_opt=get_date_framework_closed(stage, previous_framework_slug),
    )


if __name__ == "__main__":
    arguments = docopt(__doc__)

    stage = arguments["<stage>"]
    previous_framework = arguments["<previous_framework>"]
    logger = logging_helpers.configure_logger(
        {"dmapiclient": logging.INFO}
        if arguments["--verbose"]
        else {"dmapiclient": logging.WARN}
    )

    mailchimp_email_addresses = get_email_addresses_from_mailchimp(
        stage, previous_framework
    )
    output_emails_as_csv(mailchimp_email_addresses)
