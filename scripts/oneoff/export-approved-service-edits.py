#!/usr/bin/env python3

"""Get details about approved service edits in a period.

Outputs a CSV.

Usage: export-approved-service-edits.py [-h] [options] <from> [<to>]

    <from>  Beginning of time range in ISO 8601 format.
    <to>    End of time range in ISO 8601 format.

Options:
    --stage=<stage>  Stage to run script against [default: production].
    -h, --help       Show this help text.

Example:

    Count approved service edits in October 2020

    ./scripts/oneoff/export-approved-service-edits.py 2020-10 2020-11
"""


import csv
import itertools
import sys
from datetime import datetime, timedelta
from typing import Iterator, Optional

from docopt import docopt

from dmapiclient.data import DataAPIClient
from dmapiclient.audit import AuditTypes
from dmutils.email.helpers import validate_email_address
from dmutils.env_helpers import get_api_endpoint_from_stage

sys.path.insert(0, ".")

from dmscripts.helpers.auth_helpers import get_auth_token


ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DEFAULT_DATETIME = "1970-01-01T00:00:00.000000Z"


def parse_datetime(s: str) -> datetime:
    try:
        return datetime.strptime(s, ISO_FORMAT)
    except ValueError as e:
        if len(s) < len(DEFAULT_DATETIME):
            return datetime.strptime(s + DEFAULT_DATETIME[len(s):], ISO_FORMAT)
        else:
            raise e


def find_approved_service_edits(
    data_api_client, from_datetime: datetime, to_datetime: Optional[datetime] = None
) -> Iterator[dict]:
    """Find service edits approved by users in a period"""

    audit_events = data_api_client.find_audit_events_iter(
        acknowledged="true", latest_first=True, audit_type=AuditTypes.update_service
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

    # Audit events can be acknowledged at any point after they are created, and
    # because the server response is sorted by `createdAt` this means in theory
    # we would need to search every page of the response to find all
    # acknowledged in a time period. In practice service edits tend to get approved
    # by admins in fairly regular blocks, so we just fudge it a bit.
    # TODO: add an option to the api to return results sorted by `acknowledgedAt`

    search_until: datetime = from_datetime - timedelta(
        # anything more than 5 days takes a very long time
        days=5
    )
    audit_events = itertools.takewhile(
        lambda e: e["acknowledgedAt"] > search_until, audit_events
    )
    audit_events = filter(lambda e: from_datetime < e["acknowledgedAt"], audit_events)

    # sort by acknowledgedAt, this can take a while
    audit_events = sorted(audit_events, key=lambda e: e["acknowledgedAt"])

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

    audit_events = find_approved_service_edits(
        data_api_client, from_datetime, to_datetime
    )

    # filter out acknowledgedBy which aren't email addresses (more likely to be scripts)
    audit_events = filter(
        lambda e: validate_email_address(e["acknowledgedBy"]), audit_events
    )

    # write details as csv
    writer = csv.writer(sys.stdout)

    writer.writerow(
        [
            "date of edit",
            "date of approval",
            "approved by",
            "supplier name",
            "supplier ID",
            "service ID",
        ]
    )

    for e in audit_events:
        writer.writerow(
            [
                e["createdAt"],
                e["acknowledgedAt"].strftime(ISO_FORMAT),
                e["acknowledgedBy"],
                e["data"].get("supplierName"),
                e["data"].get("supplierId"),
                e["data"].get("serviceId"),
            ]
        )
