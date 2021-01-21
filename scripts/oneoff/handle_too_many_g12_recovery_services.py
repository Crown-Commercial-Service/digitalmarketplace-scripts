#!/usr/bin/env python
"""
Process the output of `get_g12_recovery_services.py`. For services with multiple drafts, choose the one with the most
completed answers. If there is a tie, the winner will be chosen arbitrarily.

Usage:
    scripts/oneoff/handle_too_many_g12_recovery_services.py <stage> <input_file> <output_file>
"""
import csv
import sys

from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt

sys.path.insert(0, ".")

from dmscripts.helpers.auth_helpers import get_auth_token


def _count_draft_answers(draft):
    non_answer_service_key_count = 17
    return len(draft["services"].keys()) - non_answer_service_key_count


def _get_most_complete_draft_id(api_client, draft_ids):
    drafts = [api_client.get_draft_service(draft_id) for draft_id in draft_ids]

    drafts.sort(key=_count_draft_answers, reverse=True)
    most_complete = drafts[0]
    updater = (
        most_complete["auditEvents"]["user"]
        if most_complete.get("auditEvents")
        else "?"
    )
    print(
        f"Choosing '{most_complete['services']['id']}', last updated by '{updater}' "
        f"with '{_count_draft_answers(most_complete)}' answers"
    )
    return most_complete["services"]["id"]


if __name__ == "__main__":
    args = docopt(__doc__)

    api_client = DataAPIClient(
        get_api_endpoint_from_stage(args["<stage>"]),
        get_auth_token("api", args["<stage>"]),
    )

    with open(args["<input_file>"]) as input_file:
        services = list(csv.DictReader(input_file))

    for service in services:
        draft_ids = service["serviceId"].split(";")

        if len(draft_ids) <= 1:
            continue

        service["serviceId"] = str(_get_most_complete_draft_id(api_client, draft_ids))

    print([s.get("serviceId") for s in services])

    with open(args["<output_file>"], "w") as output_file:
        writer = csv.DictWriter(output_file, services[0].keys())
        writer.writeheader()
        writer.writerows(services)
