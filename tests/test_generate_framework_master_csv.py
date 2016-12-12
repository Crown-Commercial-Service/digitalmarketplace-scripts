# -*- coding: utf-8 -*-
"""Tests for GenerateMasterCSV class."""
import json

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import mock

from dmscripts.generate_framework_master_csv import GenerateMasterCSV


def test_get_fieldnames(mock_data_client):
    """Test building filenames."""
    csv_builder = GenerateMasterCSV(client=mock_data_client, target_framework_slug='test_framework_slug')
    assert mock_data_client.get_framework.called_once_with('test_framework_slug')

    csv_builder.lot_name_prefixes = ['test_lot_prefix_1', 'test_lot_prefix_2']
    csv_builder.static_fieldnames = ['test_static_fieldname_1', 'test_static_fieldname_2']

    expected_data = [
        'test_static_fieldname_1',
        'test_static_fieldname_2',
        'test_lot_prefix_1_test_lot_slug_1',
        'test_lot_prefix_2_test_lot_slug_1',
        'test_lot_prefix_1_test_lot_slug_2',
        'test_lot_prefix_2_test_lot_slug_2'
    ]

    assert csv_builder.get_fieldnames() == expected_data


@mock.patch(
    'dmscripts.generate_framework_master_csv.GenerateMasterCSV.get_fieldnames',
    return_value=['test_field_1', 'test_field_2'],
)
def test_write_csv(fieldname_mock, mock_data_client):
    """Test writing csv."""
    csv_builder = GenerateMasterCSV(client=mock_data_client, target_framework_slug='test_framework_slug')
    assert fieldname_mock.called_once_with('test_framework_slug')
    csv_builder.output = [
        {'test_field_1': 'foo', 'test_field_2': 'bar'},
        {'test_field_1': 'baz', 'test_field_2': 'Ąćĉ'}
    ]
    f = StringIO()
    csv_builder.write_csv(outfile=f)

    expected_data = "test_field_1,test_field_2\nfoo,bar\nbaz,Ąćĉ\n"

    assert f.getvalue() == expected_data


def test_populate_output_suppliers(mock_data_client):
    """Test supplier info, no lot info."""
    with open('tests/fixtures/test_supplier_frameworks_response.json') as supplier_frameworks_response:
        mock_data_client.find_framework_suppliers.return_value = json.loads(supplier_frameworks_response.read())
    csv_builder = GenerateMasterCSV(client=mock_data_client, target_framework_slug='test_framework_slug')
    f = StringIO()
    csv_builder.populate_output()
    csv_builder.write_csv(outfile=f)

    with open('tests/fixtures/test_populate_output_suppliers_expected_result.csv') as expected_file:
        assert f.getvalue() == expected_file.read()


def test_one_supplier_one_lot(mock_data_client):
    """Test a single client in a single lot."""
    mock_data_client.get_framework.return_value = {
        'frameworks': {'lots': [{'slug': 'saas'}]}
    }
    mock_data_client.find_framework_suppliers.return_value = {
        'supplierFrameworks': [
            {'supplierId': 123, 'supplierName': 'Bens cool supplier', 'extraneous_field': 'foo', 'declaration': ''}
        ]
    }
    mock_data_client.find_draft_services_iter.return_value = iter([{
        'lot': 'saas', 'status': 'submitted', 'extraneous_field': 'foo'
    }])

    csv_builder = GenerateMasterCSV(client=mock_data_client, target_framework_slug='test_framework_slug')
    f = StringIO()
    csv_builder.populate_output()
    csv_builder.write_csv(outfile=f)

    with open('tests/fixtures/test_one_supplier_one_lot_result.csv') as expected_file:
        assert f.getvalue() == expected_file.read()


def test_many_suppliers_many_lots(mock_data_client):
    """Full test for creating the csv using realistic data."""
    lot_dicts = [
        {'slug': 'saas', 'extraneous_field': 'foo'},
        {'slug': 'test_lot', 'extraneous_field': 'foo'},
        {'slug': 'test_lot2', 'extraneous_field': 'foo'},
    ]
    mock_data_client.get_framework.return_value = {
        'frameworks': {'lots': lot_dicts, 'extraneous_field': 'foo'}, 'extraneous_field': 'foo'
    }
    mock_data_client.find_framework_suppliers.return_value = {
        'extraneous_field': 'foo',
        'supplierFrameworks': [
            {
                'supplierId': 123,
                'supplierName': 'Bens cool supplier1',
                'extraneous_field': 'foo',
                'declaration': {'status': 'completed'}
            },
            {'supplierId': 456, 'supplierName': 'Bens cool supplier2', 'extraneous_field': 'foo', 'declaration': ''},
            {'supplierId': 789, 'supplierName': 'Bens cool supplier3', 'extraneous_field': 'foo', 'declaration': ''},
            {'supplierId': 101, 'supplierName': 'Bens cool supplier3', 'extraneous_field': 'foo', 'declaration': ''}
        ]
    }

    # Side effect function for services so we can more accurately mimic prod.
    def service_api_side_effect(supplier_id, **kwargs):
        if supplier_id == 123:
            # Imitates a user only in one lot.
            return iter([
                {'lot': 'saas', 'status': 'submitted', 'extraneous_field': 'foo'},
                {'lot': 'saas', 'status': 'submitted', 'extraneous_field': 'foo'},
                {'lot': 'saas', 'status': 'submitted', 'extraneous_field': 'foo'},
                {'lot': 'saas', 'status': 'submitted', 'extraneous_field': 'foo'},
                {'lot': 'saas', 'status': 'submitted', 'extraneous_field': 'foo'},
                {'lot': 'saas', 'status': 'submitted', 'extraneous_field': 'foo'},
            ])
        if supplier_id == 456:
            # Immitates a heavyweight user.
            return iter([
                {'lot': 'saas', 'status': 'submitted', 'extraneous_field': 'foo'},
                {'lot': 'test_lot', 'status': 'not-submitted', 'extraneous_field': 'foo'},
                {'lot': 'test_lot', 'status': 'submitted', 'extraneous_field': 'foo'},
                {'lot': 'test_lot', 'status': 'submitted', 'extraneous_field': 'foo'},
                {'lot': 'test_lot2', 'status': 'submitted', 'extraneous_field': 'foo'},
                {'lot': 'test_lot2', 'status': 'submitted', 'extraneous_field': 'foo'},
            ])
        if supplier_id == 789:
            # Imitates a supplier with no submitted service but a started application.
            return iter([{
                'lot': 'test_lot2', 'status': 'not-submitted', 'extraneous_field': 'foo'
            }])
        if supplier_id == 101:
            # Imitates a supplier registered but with no services.
            return iter([])
        else:
            # We should not get here.
            assert False, "The csv creator recieved an invalid supplier id."
    mock_data_client.find_draft_services_iter.side_effect = service_api_side_effect

    csv_builder = GenerateMasterCSV(client=mock_data_client, target_framework_slug='test_framework_slug')
    f = StringIO()
    csv_builder.populate_output()
    csv_builder.write_csv(outfile=f)

    with open('tests/fixtures/test_many_suppliers_many_lots_result.csv') as expected_file:
        assert f.getvalue() == expected_file.read()
