# -*- coding: utf-8 -*-
"""Tests for GenerateMasterCSV class."""

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import mock

from dmscripts.generate_framework_master_csv import GenerateMasterCSV


def test_get_fieldnames(mock_data_client):
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
    csv_builder = GenerateMasterCSV(client=mock_data_client, target_framework_slug='test_framework_slug')
    assert fieldname_mock.called_once_with('test_framework_slug')

    csv_builder.output = [
        {'test_field_1': 'foo', 'test_field_2': 'bar'},
        {'test_field_1': 'baz', 'test_field_2': 'quux'}
    ]
    f = StringIO()
    csv_builder.write_csv(outfile=f)

    expected_data = "test_field_1,test_field_2\nfoo,bar\nbaz,quux\n"

    assert f.getvalue() == expected_data


