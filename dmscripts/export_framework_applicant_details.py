from itertools import chain

from dmscripts.helpers.csv_helpers import write_csv
from dmscripts.helpers.framework_helpers import find_suppliers_with_details_and_draft_service_counts

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
    "g-cloud-9": (
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
    ),
    "g-cloud-10": (
        "primaryContact",
        "primaryContactEmail",
        "supplierRegisteredName",
        "supplierRegisteredBuilding",
        "supplierRegisteredTown",
        "supplierRegisteredPostcode",
        "supplierTradingStatus",
        "supplierRegisteredCountry",
        "supplierCompanyRegistrationNumber",
        "supplierDunsNumber",
        "supplierVatNumber",
        "supplierOrganisationSize",
        "subcontracting",
        "contactNameContractNotice",
        "contactEmailContractNotice",
    ),
    "digital-outcomes-and-specialists-3": (
        "primaryContact",
        "primaryContactEmail",
        "supplierRegisteredName",
        "supplierRegisteredBuilding",
        "supplierRegisteredTown",
        "supplierRegisteredPostcode",
        "supplierTradingStatus",
        "supplierRegisteredCountry",
        "supplierCompanyRegistrationNumber",
        "supplierDunsNumber",
        "supplierVatNumber",
        "supplierOrganisationSize",
        "subcontracting",
        "contactNameContractNotice",
        "contactEmailContractNotice",
        "cyberEssentials",
        "cyberEssentialsPlus",
    ),
}


def get_csv_rows(records, framework_slug, framework_lot_slugs, count_statuses=("submitted", "failed",)):
    """
    :param count_statuses: tuple of draft service statuses that should be counted. The default ("submitted", "failed")
                           gives a count of all drafts that were originally submitted.
    """
    rows_iter = (
        _create_row(framework_slug, record, count_statuses, framework_lot_slugs)
        for record in records
        if record['declaration'].get('status') == 'complete'
        # only include the record if it has at least one count with a required status
        and any(status in count_statuses for (lot, status) in record['counts'])
    )
    headers = tuple(chain(
        (
            "supplier_id",
            "supplier_name",
            'supplier_contact_name',
            'supplier_email',
            "pass_fail",
            "countersigned_at",
            "countersigned_path",
        ),
        (lot_slug for lot_slug in framework_lot_slugs),
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


def _create_row(framework_slug, record, count_statuses, framework_lot_slugs):
    return dict(chain(
        (
            ("supplier_id", record["supplier"]["id"]),
            ("supplier_name", record["supplier"]["name"]),
            ("supplier_contact_name", record["supplier"]["contactInformation"][0]['contactName']),
            ("supplier_email", record["supplier"]["contactInformation"][0]['email']),
            ("pass_fail", _pass_fail_from_record(record)),
            ("countersigned_at", record["countersignedAt"]),
            ("countersigned_path", record["countersignedPath"]),
        ),
        (
            (lot, sum(record["counts"][(lot, status)] for status in count_statuses))
            for lot in framework_lot_slugs
        ),
        ((field, record["declaration"].get(field, "")) for field in DECLARATION_FIELDS[framework_slug]),
    ))


def export_supplier_details(data_api_client, framework_slug, filename, framework_lot_slugs):
    records = find_suppliers_with_details_and_draft_service_counts(data_api_client, framework_slug)
    headers, rows_iter = get_csv_rows(records, framework_slug, framework_lot_slugs)
    write_csv(headers, rows_iter, filename)
