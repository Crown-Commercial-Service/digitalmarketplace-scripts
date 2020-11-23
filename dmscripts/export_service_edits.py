import csv
import datetime
import difflib
from typing import Iterator, Optional

from dmapiclient.audit import AuditTypes
from dmutils.email.helpers import validate_email_address

from dmscripts.helpers.datetime_helpers import audit_date


def filter_scripts_from_service_edits(audit_events):
    # filter out acknowledgedBy which aren't email addresses (more likely to be scripts)
    return filter(
        lambda e: validate_email_address(e["acknowledgedBy"]), audit_events
    )


def find_service_edits(
    data_api_client,
    service_id: str,
    from_date: Optional[datetime.date] = None,
    to_date: Optional[datetime.date] = None,
    *,
    latest_first=True,
    exclude_scripts=True,
) -> Iterator:
    """Generate a list of edits to a service

    Find changes made to a service, optionally within a time period. By default
    the most recent change is returned first.

    If `exclude_scripts` is true then service edits which were made by scripts
    will not be included in the result.
    """
    # I think this is the easiest way to get service edits
    audit_events = data_api_client.find_audit_events_iter(
        audit_date=audit_date(from_date, to_date),
        audit_type=AuditTypes.update_service,
        latest_first=latest_first,
        object_type="services",
        object_id=service_id,
    )

    if exclude_scripts:
        audit_events = filter_scripts_from_service_edits(audit_events)

    return audit_events


def diff_archived_services(a: dict, b: dict) -> str:
    if "services" in a:
        a = a["services"]
    if "services" in b:
        b = b["services"]
    if not (a["frameworkFamily"] == b["frameworkFamily"] and a["lot"] == b["lot"]):
        raise ValueError("archived services to compare must be from same framework family and lot")

    assert a.keys() == b.keys()

    def do_diff(a, b, key) -> str:
        assert type(a) == type(b)
        assert a != b
        if isinstance(a, list):
            addnewlines = lambda l: list(map(lambda s: s + "\n", l))  # noqa: E731
            return "".join(difflib.Differ().compare(addnewlines(a), addnewlines(b)))
        elif isinstance(a, str):
            addnewline = lambda s: s + "\n" if not s.endswith("\n") else s  # noqa: E731
            return "".join(difflib.Differ().compare(
                addnewline(a).splitlines(keepends=True),
                addnewline(b).splitlines(keepends=True)
            ))
        else:
            raise TypeError(f"cannot compare type '{type(a)}' at '{key}'")

    changes = (
        "\n\n".join(
            f"{k}:\n{do_diff(a[k], b[k], k)}"
            for k in a
            if a[k] != b[k]
            and k not in ("links", "updatedAt")
        )
    )

    return changes


def service_edit_diff(data_api_client, audit_event) -> str:
    assert audit_event["type"] == "update_service"

    new = data_api_client.get_archived_service(audit_event["data"]["newArchivedServiceId"])
    old = data_api_client.get_archived_service(audit_event["data"]["oldArchivedServiceId"])

    return diff_archived_services(new, old)


def write_service_edits_csv(f, audit_events, data_api_client, *, include_diffs=True):
    """Write a CSV including details of service edits to `f`

    Optionally includes the textual changes in a simple diff-like format.
    """
    writer = csv.writer(f)

    writer.writerow(
        [
            "date of edit",
            "date of approval",
            "approved by",
            "supplier name",
            "supplier ID",
            "service ID",
        ] + [
            "service changes",
        ] if include_diffs else []
    )

    for e in audit_events:
        writer.writerow(
            [
                e["createdAt"],
                e["acknowledgedAt"],
                e["acknowledgedBy"],
                e["data"].get("supplierName"),
                e["data"].get("supplierId"),
                e["data"].get("serviceId"),
            ] + [
                service_edit_diff(data_api_client, e),
            ] if include_diffs else []
        )
