import sys
if sys.version_info[0] < 3:
    import unicodecsv as csv
else:
    import csv

from multiprocessing.pool import ThreadPool
from dmutils.formats import dateformat


LOTS = {
    "g-cloud-8": ("saas", "paas", "iaas", "scs",),
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
}


def find_suppliers(client, framework_slug):
    suppliers = client.get_interested_suppliers(framework_slug)['interestedSuppliers']
    return ({'supplier_id': supplier_id} for supplier_id in suppliers)


def add_supplier_info(client):
    def inner(record):
        supplier = client.get_supplier(record['supplier_id'])

        return dict(record,
                    supplier=supplier['suppliers'])

    return inner


def add_framework_info(client, framework_slug):
    def inner(record):
        supplier_framework = client.get_supplier_framework_info(record['supplier_id'], framework_slug)
        supplier_framework = supplier_framework['frameworkInterest']
        supplier_framework['declaration'] = supplier_framework['declaration'] or {}
        supplier_framework['countersignedPath'] = supplier_framework['countersignedPath'] or ''
        supplier_framework['countersignedAt'] = dateformat(supplier_framework['countersignedAt']) or ''

        return dict(record,
                    declaration=supplier_framework['declaration'],
                    onFramework=supplier_framework['onFramework'],
                    countersignedPath=supplier_framework['countersignedPath'],
                    countersignedAt=supplier_framework['countersignedAt'],
                    )

    return inner


def add_submitted_draft_counts(client, framework_slug):
    def inner(record):
        counts = {lot: 0 for lot in LOTS[framework_slug]}

        for draft in client.find_draft_services_iter(record['supplier']['id'], framework=framework_slug):
            if draft['status'] == 'submitted':
                counts[draft['lot']] += 1

        return dict(record, counts=counts)

    return inner


def get_csv_rows(records, framework_slug):
    rows = [create_row(record, framework_slug)
            for record in records
            if record['declaration'].get('status') == 'complete'
            and sum(record['counts'].values()) > 0
            ]
    headers = (
        "supplier_id",
        "supplier_name",
        "on_framework",
        "countersigned_at",
        "countersigned_path",
        ) + LOTS[framework_slug] + DECLARATION_FIELDS[framework_slug]

    return headers, rows


def create_row(record, framework_slug):
    row = {
        'supplier_id': record['supplier']['id'],
        'supplier_name': record['supplier']['name'],
        'on_framework': record['onFramework'],
        'countersigned_at': record['countersignedAt'],
        'countersigned_path': record['countersignedPath'],
    }
    row.update({(lot, record['counts'][lot]) for lot in LOTS[framework_slug]})
    row.update(((field, record['declaration'].get(field, "")) for field in DECLARATION_FIELDS[framework_slug]))
    return dict(row)


def find_suppliers_with_details(client, framework_slug):
    pool = ThreadPool(30)

    records = find_suppliers(client, framework_slug)
    records = pool.imap(add_supplier_info(client), records)
    records = pool.imap(add_framework_info(client, framework_slug), records)
    records = pool.imap(add_submitted_draft_counts(client, framework_slug), records)

    return get_csv_rows(records, framework_slug)


def write_csv(headers, rows, filename):
    """Write a list of rows out to CSV"""

    writer = None
    with open(filename, "w+") as f:
        for row in rows:
            if writer is None:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
            writer.writerow(dict(row))


def export_supplier_details(data_api_client, framework_slug, filename):
    headers, rows = find_suppliers_with_details(data_api_client, framework_slug)
    write_csv(headers, rows, filename)
