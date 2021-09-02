#!/usr/bin/env python3
"""
Get the email addresses of everyone we will notify about a new framework coming. This is all suppliers on the previous
framework, as well as everyone who's registered interest since the previous framework closed. Outputs to stdout.

Usage:
    /generate-email-list-for-coming.py <stage> <previous_framework> [--verbose]

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


def get_date_framework_closed(data_api_client, framework_slug):
    framework = data_api_client.get_framework(framework_slug)["frameworks"]
    return isoparse(framework["applicationsCloseAtUTC"])


def get_email_addresses_from_mailchimp(
    data_api_client, dm_mailchimp_client, stage, previous_framework_slug
):
    audience_id = PRODUCTION_AUDIENCE_ID if stage == "production" else TEST_AUDIENCE_ID
    return dm_mailchimp_client.get_email_addresses_from_list(
        audience_id,
        status="subscribed",
        # Exclude people who've already been contacted about previous frameworks. We assume that they would have applied
        # to the previous framework if they were interested.
        since_timestamp_opt=get_date_framework_closed(
            data_api_client, previous_framework_slug
        ),
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

    data_api_client = DataAPIClient(
        get_api_endpoint_from_stage(stage), get_auth_token("api", stage)
    )
    (username, api_key) = get_mailchimp_credentials(stage)
    dm_mailchimp_client = DMMailChimpClient(
        username,
        api_key,
        logger,
    )

    registered_interest_email_addresses = set(
        get_email_addresses_from_mailchimp(
            data_api_client, dm_mailchimp_client, stage, previous_framework
        )
    )
    existing_supplier_email_addresses = {
        user["email address"]
        for user in data_api_client.export_users_iter(previous_framework)
    }

    output_emails_as_csv(
        registered_interest_email_addresses.union(existing_supplier_email_addresses)
    )
