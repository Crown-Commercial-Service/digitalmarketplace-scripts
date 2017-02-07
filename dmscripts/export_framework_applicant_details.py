from itertools import chain
import sys
if sys.version_info[0] < 3:
    import unicodecsv as csv
else:
    import csv

from dmscripts.helpers.framework_helpers import find_suppliers_with_details_and_draft_service_counts

LOTS = {
    "g-cloud-8": ("saas", "paas", "iaas", "scs",),
    "digital-outcomes-and-specialists-2": (
        "digital-outcomes",
        "digital-specialists",
        "user-research-participants",
        "user-research-studios",
    ),
}

DECLARATION_FIELDS = {
    "g-cloud-8": (
        "primaryContact",
        "primaryContactEmail",
        "nameOfOrganisation",
        "registeredAddressBuilding",
        "registeredAddressTown",
        "registeredAddressPostcode",
        "tradingStatus",
        "tradingStatusOther",
        "tradingNames",
        "firstRegistered",
        "currentRegisteredCountry",
        "companyRegistrationNumber",
        "dunsNumber",
        "registeredVATNumber",
        "establishedInTheUK",
        "appropriateTradeRegisters",
        "appropriateTradeRegistersNumber",
        "licenceOrMemberRequired",
        "licenceOrMemberRequiredDetails",
        "organisationSize",
        "subcontracting",
        "contactNameContractNotice",
        "contactEmailContractNotice",
        "cyberEssentials",
        "cyberEssentialsPlus",
    ),
    "digital-outcomes-and-specialists-2": (
        "primaryContact",
        "primaryContactEmail",
        "nameOfOrganisation",
        "registeredAddressBuilding",
        "registeredAddressTown",
        "registeredAddressPostcode",
        "tradingStatus",
        "tradingStatusOther",
        "tradingNames",
        "firstRegistered",
        "currentRegisteredCountry",
        "companyRegistrationNumber",
        "dunsNumber",
        "registeredVATNumber",
        "establishedInTheUK",
        "appropriateTradeRegisters",
        "appropriateTradeRegistersNumber",
        "licenceOrMemberRequired",
        "licenceOrMemberRequiredDetails",
        "organisationSize",
        "subcontracting",
        "contactNameContractNotice",
        "contactEmailContractNotice",
        "cyberEssentials",
        "cyberEssentialsPlus",
    ),
}


def get_csv_rows(records, framework_slug):
    rows_iter = (
        create_row(framework_slug, record)
        for record in records
        if record['declaration'].get('status') == 'complete' and record['counts']  # i.e. has submitted any services
    )
    headers = tuple(chain(
        (
            "supplier_id",
            "supplier_name",
            "pass_fail",
            "countersigned_at",
            "countersigned_path",
        ),
        (lot_slug for lot_slug in LOTS[framework_slug]),
        DECLARATION_FIELDS[framework_slug],
    ))

    return headers, rows_iter


def _pass_fail_from_record(record):
    if record["onFramework"] is False:
        return "fail"
    else:
        return (
            "pass" if record["onFramework"] else "discretionary"
        ) + (
            "" if all(
                status != "failed" for (lot_slug, status), v in record['counts'].items()
            ) else "_with_failed_services"
        )


def create_row(framework_slug, record):
    return dict(chain(
        (
            ("supplier_id", record["supplier"]["id"]),
            ("supplier_name", record["supplier"]["name"]),
            ("pass_fail", _pass_fail_from_record(record)),
            ("countersigned_at", record["countersignedAt"]),
            ("countersigned_path", record["countersignedPath"]),
        ),
        (
            (lot, sum(record["counts"][(lot, status)] for status in ("submitted", "failed",)))
            for lot in LOTS[framework_slug]
        ),
        ((field, record["declaration"].get(field, "")) for field in DECLARATION_FIELDS[framework_slug]),
    ))


def write_csv(headers, rows_iter, filename):
    """Write a list of rows out to CSV"""

    writer = None
    with open(filename, "w+") as f:
        for row in rows_iter:
            if writer is None:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
            writer.writerow(dict(row))


def export_supplier_details(data_api_client, framework_slug, filename):
    records = find_suppliers_with_details_and_draft_service_counts(data_api_client, framework_slug)
    headers, rows_iter = get_csv_rows(records, framework_slug)
    write_csv(headers, rows_iter, filename)
