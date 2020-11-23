#!/usr/bin/env python3

"""Get details about edits to a service in a period.

Outputs a CSV.

Usage: export-service-edits.py [-h] [options] <service_id> [<from>] [<to>]

    <service_id>  Public ID of the service.
    <from>        Beginning of time range in ISO 8601 format.
    <to>          End of time range in ISO 8601 format.

Options:
    --stage=<stage>  Stage to run script against [default: production].
    -h, --help       Show this help text.

Example:

    Write service edits since October 2020 to a file

    ./scripts/oneoff/export-approved-service-edits.py 11111111111 2020-10 > service_edits_11111111111.csv
"""
import sys

from docopt import docopt

from dmapiclient.data import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage

sys.path.insert(0, ".")

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.datetime_helpers import parse_datetime
from dmscripts.export_service_edits import find_service_edits, write_service_edits_csv

if __name__ == "__main__":

    args = docopt(__doc__)

    stage = args["--stage"]

    from_datetime = parse_datetime(args["<from>"]) if args["<from>"] else None
    to_datetime = parse_datetime(args["<to>"]) if args["<to>"] else None

    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token("api", stage),
    )

    audit_events = find_service_edits(
        data_api_client, args["<service_id>"],
        from_datetime, to_datetime
    )

    write_service_edits_csv(sys.stdout, audit_events, data_api_client)
