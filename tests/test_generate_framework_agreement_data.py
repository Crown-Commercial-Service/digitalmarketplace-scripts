from dmapiclient import HTTPError

from dmscripts.generate_framework_agreement_data import (
    make_filename_key,
    read_csv, supplier_is_on_framework)


def test_read_csv():
    assert read_csv('tests/fixtures/framework_results.csv') == [
        ['123', 'Supplier Name', 'pass'],
        ['234', 'Supplier Name', 'fail'],
        ['345', 'Supplier Name', ' PASS'],
        ['456', 'Supplier Name', ' FAIL'],
        ['567', 'Supplier Name', ' Yes'],
        ['Company Name', 'Supplier Name', 'pass'],
        ['678', 'Supplier Name', 'PasS'],
    ]


def test_make_filename_key():
    assert make_filename_key('Kev\'s Butties', 1234) == 'Kevs_Butties-1234'
    assert make_filename_key('   Supplier A   ', 1234) == 'Supplier_A-1234'
    assert make_filename_key('Kev & Sons. | Ltd', 1234) == 'Kev_and_Sons_Ltd-1234'
    assert make_filename_key('\ / : * ? \' " < > |', 1234) == '_-1234'
    assert make_filename_key('kev@the*agency', 1234) == 'kevtheagency-1234'


def test_supplier_is_on_framework(mock_data_client):
    mock_data_client.get_supplier_framework_info.return_value = {'frameworkInterest': {'onFramework': True}}
    assert supplier_is_on_framework(mock_data_client, 123) is True

    mock_data_client.get_supplier_framework_info.return_value = {'frameworkInterest': {'onFramework': False}}
    assert supplier_is_on_framework(mock_data_client, 123) is False

    mock_data_client.get_supplier_framework_info.return_value = {'frameworkInterest': {'onFramework': None}}
    assert supplier_is_on_framework(mock_data_client, 123) is None

    mock_data_client.get_supplier_framework_info.side_effect = HTTPError()
    assert supplier_is_on_framework(mock_data_client, 123) is False
