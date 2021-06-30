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
from dmscripts.helpers.datetime_helpers import ISO_FORMAT, parse_datetime
from dmscripts.export_service_edits import write_service_edits_csv


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

    audit_events = find_approved_service_edits(
        data_api_client, from_datetime, to_datetime
    )

    # filter out acknowledgedBy which aren't email addresses (more likely to be scripts)
    audit_events = filter(
        lambda e: validate_email_address(e["acknowledgedBy"]), audit_events
    )

    write_service_edits_csv(sys.stdout, audit_events, data_api_client)
