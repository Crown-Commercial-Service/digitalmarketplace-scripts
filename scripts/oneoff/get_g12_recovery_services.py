#!/usr/bin/env python
"""
Get the drafts that correspond to G12 recovery services. Note that there can be 0 or multiple drafts for one service.
You will need to process the output to get a one-to-one mapping.

Usage:
    scripts/get_g12_recovery_services.py <stage> <phase_file> <output_file>
"""
import csv
import sys

from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt

sys.path.insert(0, ".")

from dmscripts.helpers.auth_helpers import get_auth_token


def _normalise_service_name(name):
    """
    To be able to safely compare service names. The output is not meant to be human-readable.

    Copied from `upload_draft_service_pdfs.py`
    """
    return (
        name.lower()
        .replace("-", "")
        .replace("_", "")
        .replace(":", "")
        .replace(" ", "")
        .replace(".csv", "")
    )


def get_drafts_for_supplier(supplier_id, api_client):
    return api_client.find_draft_services_by_framework(
        "g-cloud-12", supplier_id=supplier_id, status="not-submitted"
    )["services"]


if __name__ == "__main__":
    args = docopt(__doc__)

    api_client = DataAPIClient(
        get_api_endpoint_from_stage(args["<stage>"]),
        get_auth_token("api", args["<stage>"]),
    )

    with open(args["<phase_file>"]) as phase_file:
        services = list(csv.DictReader(phase_file))

    suppliers = {service["Supplier ID"] for service in services}

    for supplier_id in suppliers:
        expected_services = [
            service for service in services if service["Supplier ID"] == supplier_id
        ]
        actual_drafts = get_drafts_for_supplier(supplier_id, api_client)

        for expected_service in expected_services:
            matching_drafts = [
                str(draft["id"])
                for draft in actual_drafts
                if _normalise_service_name(draft["serviceName"])
                == _normalise_service_name(expected_service["Service Name"])
            ]

            expected_service["serviceId"] = ";".join(matching_drafts)

    print([s.get("serviceId") for s in services])

    with open(args["<output_file>"], "w") as output_file:
        writer = csv.DictWriter(output_file, services[0].keys())
        writer.writeheader()
        writer.writerows(services)
