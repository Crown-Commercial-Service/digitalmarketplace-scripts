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


def add_defaults_for_keys(old: dict, new: dict):
    """
    Users can add/remove answers to optional questions. Add defaults so we can diff them.
    """
    for new_key in new.keys() - old.keys():
        if isinstance(new[new_key], list):
            old[new_key] = []
        else:
            old[new_key] = ""

    for old_key in old.keys() - new.keys():
        if isinstance(old[old_key], list):
            new[old_key] = []
        else:
            new[old_key] = ""


def diff_archived_services(old: dict, new: dict) -> str:
    if "services" in old:
        old = old["services"]
    if "services" in new:
        new = new["services"]
    if not (old["frameworkFamily"] == new["frameworkFamily"] and old["lot"] == new["lot"]):
        raise ValueError("archived services to compare must be from same framework family and lot")

    add_defaults_for_keys(old, new)

    def do_diff(old, new, key) -> str:
        assert type(old) == type(new)
        assert old != new
        if isinstance(old, list):
            addnewlines = lambda l: list(map(lambda s: s + "\n", l))  # noqa: E731
            return "".join(difflib.Differ().compare(addnewlines(old), addnewlines(new)))
        elif isinstance(old, str):
            addnewline = lambda s: s + "\n" if not s.endswith("\n") else s  # noqa: E731
            return "".join(difflib.Differ().compare(
                addnewline(old).splitlines(keepends=True),
                addnewline(new).splitlines(keepends=True)
            ))
        else:
            raise TypeError(f"cannot compare type '{type(old)}' at '{key}'")

    changes = (
        "\n\n".join(
            f"{k}:\n{do_diff(old[k], new[k], k)}"
            for k in old
            if old[k] != new[k]
            and k not in ("links", "updatedAt")
        )
    )

    return changes


def service_edit_diff(data_api_client, audit_event) -> str:
    assert audit_event["type"] == "update_service"

    new = data_api_client.get_archived_service(audit_event["data"]["newArchivedServiceId"])
    old = data_api_client.get_archived_service(audit_event["data"]["oldArchivedServiceId"])

    return diff_archived_services(old, new)


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
