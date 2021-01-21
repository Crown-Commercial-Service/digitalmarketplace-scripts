#!/usr/bin/env python
"""
Process the output of `get_g12_recovery_services.py`. Create new empty drafts for all services that do not yet have a
draft.

Usage:
    scripts/oneoff/handle_missing_g12_recovery_services.py <stage> <input_file> <output_file> [--dry-run]
"""
import csv
import sys

from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt

sys.path.insert(0, ".")

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.updated_by_helpers import get_user


if __name__ == "__main__":
    args = docopt(__doc__)

    api_client = DataAPIClient(
        get_api_endpoint_from_stage(args["<stage>"]),
        get_auth_token("api", args["<stage>"]),
        user=get_user(),
    )

    with open(args["<input_file>"]) as input_file:
        services = list(csv.DictReader(input_file))

    missing_services = [s for s in services if not s["serviceId"]]

    for service in missing_services:
        name = service["Service Name"].replace(".csv", "")[:100]
        supplier_id = service["Supplier ID"]
        lot = {
            "Software": "cloud-software",
            "Support": "cloud-support",
        }.get(service["Lot"])

        if not lot:
            print(f"No lot for '{name}'/'{service['File Name']}' - {supplier_id}")
            continue

        if args["--dry-run"]:
            print(f"Would create '{name}'")
            continue

        new_draft = api_client.create_new_draft_service(
            "g-cloud-12", lot, supplier_id, {"serviceName": name}
        )["services"]
        print(f"Created '{name}': {new_draft['id']}")
        service["serviceId"] = str(new_draft["id"])

    print([s.get("serviceId") for s in services])

    with open(args["<output_file>"], "w") as output_file:
        writer = csv.DictWriter(output_file, services[0].keys())
        writer.writeheader()
        writer.writerows(services)
