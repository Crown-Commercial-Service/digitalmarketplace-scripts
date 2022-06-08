#!/usr/bin/env python3

"""Produce a report of all approved service edits in a period, upload it to S3, and send an email with the download link
to category admins.

Usage: export-approved-service-edits.py [-h] [options] <from> [<to>]

    <from>  Beginning of time range in ISO 8601 format.
    <to>    End of time range in ISO 8601 format.

Options:
    --stage=<stage>  Stage to run script against [default: production].
    -h, --help       Show this help text.

Example:

    Count approved service edits in October 2020

    ./scripts/export-approved-service-edits.py 2020-10 2020-11
"""
import io
import itertools
import sys
from datetime import datetime
from typing import Iterator, Optional

from docopt import docopt

from dmapiclient.data import DataAPIClient
from dmapiclient.audit import AuditTypes
from dmutils.email.helpers import validate_email_address
from dmutils.env_helpers import get_api_endpoint_from_stage, get_web_url_from_stage
from dmutils.s3 import S3

sys.path.insert(0, ".")

from dmscripts.helpers import logging_helpers
from dmscripts.helpers.auth_helpers import get_auth_token, get_jenkins_env_variable
from dmscripts.helpers.datetime_helpers import ISO_FORMAT, parse_datetime
from dmscripts.helpers.email_helpers import scripts_notify_client
from dmscripts.helpers.s3_helpers import get_bucket_name
from dmscripts.export_service_edits import write_service_edits_csv


logger = logging_helpers.configure_logger({
    'dmapiclient.base': logging_helpers.logging.WARNING,
})

NOTIFY_TEMPLATE_ID = "fe4b0ac2-c25f-4b02-a72d-0d5b19819d74"  # A new approved service edit report is available
REPORT_EMAIL = "digitalmarketplace-service-edit-reports@crowncommercial.gov.uk"


def find_approved_service_edits(
    data_api_client, from_datetime: datetime, to_datetime: Optional[datetime] = None
) -> Iterator[dict]:
    """Find service edits approved by users in a period"""

    audit_events = data_api_client.find_audit_events_iter(
        acknowledged="true", latest_first=True, audit_type=AuditTypes.update_service, sort_by="acknowledged_at"
    )

    # use datetimes to make our life easier
    audit_events = map(
        lambda e: {
            **e,
            "acknowledgedAt": datetime.strptime(e["acknowledgedAt"], ISO_FORMAT),
        },
        audit_events,
    )

    if to_datetime:
        audit_events = filter(lambda e: e["acknowledgedAt"] < to_datetime, audit_events)

    audit_events = itertools.takewhile(
        lambda e: e["acknowledgedAt"] > from_datetime, audit_events
    )
    return audit_events


if __name__ == "__main__":
    args = docopt(__doc__)

    stage = args["--stage"]

    from_datetime: datetime = parse_datetime(args["<from>"])
    to_datetime: Optional[datetime] = (
        parse_datetime(args["<to>"]) if args["<to>"] else None
    )

    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token("api", stage),
    )

    notify_api_token = get_jenkins_env_variable("NOTIFY_API_TOKEN", require_jenkins_user=False)
    notify_client = scripts_notify_client(notify_api_token, logger=logger)

    audit_events = find_approved_service_edits(
        data_api_client, from_datetime, to_datetime
    )

    # filter out acknowledgedBy which aren't email addresses (more likely to be scripts)
    audit_events = filter(
        lambda e: validate_email_address(e["acknowledgedBy"]), audit_events
    )

    report_csv = io.StringIO()
    write_service_edits_csv(report_csv, audit_events, data_api_client)

    bucket = S3(get_bucket_name(stage, "reports"))
    s3_file_name = f"approved-service-edits-{args['<from>']}.csv"
    s3_file_path = f"common/reports/{s3_file_name}"
    bucket.save(
        s3_file_path,
        io.BytesIO(report_csv.getvalue().encode('utf-8')),
        acl='bucket-owner-full-control',
        download_filename=s3_file_name
    )

    logger.info(f"Successfully uploaded report to: {bucket.bucket_name}/{s3_file_path}")

    admin_link = f"{get_web_url_from_stage(stage)}/admin/services/updates/approved/{args['<from>']}"
    logger.info(f"Category admins can download the report from: {admin_link}")
    notify_client.send_email(REPORT_EMAIL, NOTIFY_TEMPLATE_ID, personalisation={"report_url": admin_link})
