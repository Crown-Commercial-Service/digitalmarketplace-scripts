from itertools import chain

from dmscripts.helpers.csv_helpers import write_csv
from dmscripts.helpers.framework_helpers import find_suppliers_with_details_and_draft_service_counts
from dmscripts.helpers.supplier_data_helpers import country_code_to_name
from dmscripts.helpers.logging_helpers import get_logger

logger = get_logger()

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
    ),
    "g-cloud-11": (
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
        "supplierOrganisationSize",
        "subcontracting",
        "contactNameContractNotice",
        "contactEmailContractNotice",
    ),
}

SUPPLIER_ACCOUNT_FIELDS = (
    'supplier_registered_name',
    'supplier_registration_number',
    'supplier_contact_address1',
    'supplier_contact_city',
    'supplier_contact_postcode'
)


def get_csv_rows(
    records,
    framework_slug,
    framework_lot_slugs,
    count_statuses=("submitted", "failed",),
    dry_run=False,
    include_central_supplier_details=False,
):
    """
    :param count_statuses:                      tuple of draft service statuses that should be
                                                counted. The default ("submitted", "failed") gives
                                                a count of all drafts that were originally
                                                submitted.
    :param dry_run:                             if True the records will be returned without
                                                declaration information.
    :param include_central_supplier_details:    include contact info from supplier account (i.e. not the declaration)

    :returns:                                   row headers and rows as a sequence of dictionaries
                                                with the headers as keys.
    :rtype:                                     tuple[tuple[str], iterable[dict]]
    """
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
        (
            supplier_account_field for supplier_account_field in SUPPLIER_ACCOUNT_FIELDS
            if include_central_supplier_details
        )
    ))

    # filter records eagerly
    records = [
        record
        for record in records
        if record['declaration'].get('status') == 'complete'
        # only include the record if it has at least one count with a required status
        and any(status in count_statuses for (lot, status) in record['counts'])
    ]

    logger.info(f"found {len(records)} supplier records to process")

    rows_iter = (
        _create_row(
            framework_slug, record, count_statuses, framework_lot_slugs, dry_run, include_central_supplier_details
        )
        for record in records
    )

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


def _format_field(field_name, field_value):
    if field_name == 'supplierRegisteredCountry' and field_value:
        field_value = country_code_to_name(field_value)

    return field_name, field_value


def _create_row(
    framework_slug, record, count_statuses, framework_lot_slugs, dry_run=False, include_central_supplier_details=False
):
    """
    Fetch supplier data from central details, contact information and declaration
    :param dry_run:                             if True return row without declaration information
    :param include_central_supplier_details:    include contact info from supplier account (i.e. not the declaration)
    """
    row = {
        "supplier_id": record["supplier"]["id"],
        "supplier_name": record["supplier"]["name"],
        "supplier_contact_name": record["supplier"]["contactInformation"][0]['contactName'],
        "supplier_email": record["supplier"]["contactInformation"][0]['email'],
        "pass_fail": _pass_fail_from_record(record),
        "countersigned_at": record["countersignedAt"],
        "countersigned_path": record["countersignedPath"],
    }
    row.update(
        (lot, sum(record["counts"][(lot, status)] for status in count_statuses))
        for lot in framework_lot_slugs
    )
    if dry_run:
        return row

    # attach declaration information
    row.update(
        _format_field(field, record["declaration"].get(field, ""))
        for field in DECLARATION_FIELDS[framework_slug]
    )

    # For regenerating framework agreements with updated information (instead of the declaration details)
    if include_central_supplier_details:
        row.update({
            "supplier_registered_name": record["supplier"]["registeredName"],
            "supplier_registration_number": record["supplier"].get(
                'companiesHouseNumber',
                record["supplier"].get('otherCompanyRegistrationNumber', "")
            ),
            "supplier_contact_address1": record["supplier"]["contactInformation"][0]['address1'],
            "supplier_contact_city": record["supplier"]["contactInformation"][0]['city'],
            "supplier_contact_postcode": record["supplier"]["contactInformation"][0]['postcode'],
        })

    return row


def export_supplier_details(data_api_client, framework_slug, filename, framework_lot_slugs, map_impl=map):
    records = find_suppliers_with_details_and_draft_service_counts(data_api_client, framework_slug, map_impl=map_impl)
    headers, rows_iter = get_csv_rows(records, framework_slug, framework_lot_slugs)
    write_csv(headers, rows_iter, filename)
