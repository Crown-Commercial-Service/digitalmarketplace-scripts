from collections import Counter
import mock

from dmscripts.export_framework_applicant_details import export_supplier_details, get_csv_rows


def test_get_csv_rows_returns_headers_and_rows():
    example_record = {
        "declaration": {"status": "complete"},
        "supplier": {
            "id": 12345,
            "name": "Kev's Butties",
            "contactInformation": [{"contactName": "Kev", "email": "kev@example.com"}]
        },
        "countersignedAt": "2019-01-01",
        "countersignedPath": "/path/to/thing",
        'counts': Counter(
            {
                ('lot-1', 'submitted'): 3,
                ('lot-2', 'submitted'): 2,
                ('lot-1', 'not-submitted'): 1,
                ('lot-2', 'not-submitted'): 1
            }
        ),
        'onFramework': True
    }
    expected_headers = (
        "supplier_id",
        "supplier_name",
        'supplier_contact_name',
        'supplier_email',
        "pass_fail",
        "countersigned_at",
        "countersigned_path",
        "lot-1",
        "lot-2",
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
    )
    expected_row = {
        'contactEmailContractNotice': '',
        'contactNameContractNotice': '',
        'countersigned_at': '2019-01-01',
        'countersigned_path': '/path/to/thing',
        'lot-1': 3,
        'lot-2': 2,
        'pass_fail': 'pass',
        'primaryContact': '',
        'primaryContactEmail': '',
        'subcontracting': '',
        'supplierCompanyRegistrationNumber': '',
        'supplierDunsNumber': '',
        'supplierOrganisationSize': '',
        'supplierRegisteredBuilding': '',
        'supplierRegisteredCountry': '',
        'supplierRegisteredName': '',
        'supplierRegisteredPostcode': '',
        'supplierRegisteredTown': '',
        'supplierTradingStatus': '',
        'supplier_contact_name': 'Kev',
        'supplier_email': 'kev@example.com',
        'supplier_id': 12345,
        'supplier_name': "Kev's Butties"
    }
    headers, rows = get_csv_rows([example_record], 'g-things-23', ["lot-1", "lot-2"])
    assert headers == expected_headers
    assert next(rows) == expected_row


@mock.patch('dmscripts.export_framework_applicant_details.write_csv')
@mock.patch('dmscripts.export_framework_applicant_details.get_csv_rows')
@mock.patch('dmscripts.export_framework_applicant_details.find_suppliers_with_details_and_draft_service_counts')
def test_export_supplier_details_calls_helper_functions(find_suppliers, get_csv_rows, write_csv):
    data_api_client = mock.Mock()
    get_csv_rows.return_value = ['header1', 'header2'], 'rows_iter'
    export_supplier_details(data_api_client, 'g-things-23', "filename.csv", "lot-1,lot-2")

    find_suppliers.assert_called_once_with(data_api_client, 'g-things-23', map_impl=mock.ANY)
    get_csv_rows.assert_called_once_with(find_suppliers.return_value, 'g-things-23', "lot-1,lot-2")
    write_csv.assert_called_once_with(['header1', 'header2'], 'rows_iter', "filename.csv")
