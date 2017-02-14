import pytest

import dmscripts.helpers.csv_helpers as csv_helpers


@pytest.mark.parametrize('record,count', [
    ({"services": [
        {"theId": ["Label", "other"]},
        {"theId": ["other"]},
        {"theId": ["Label"]},
    ]}, 2),
    ({"services": []}, 0),
    ({"services": [{}]}, 0),
])
def test_count_field_in_record(record, count):
    assert csv_helpers.count_field_in_record("theId", "Label", record) == count


def test_read_csv():
    assert csv_helpers.read_csv('tests/fixtures/framework_results.csv') == [
        ['123', 'Supplier Name', 'pass'],
        ['234', 'Supplier Name', 'fail'],
        ['345', 'Supplier Name', ' PASS'],
        ['456', 'Supplier Name', ' FAIL'],
        ['567', 'Supplier Name', ' Yes'],
        ['Company Name', 'Supplier Name', 'pass'],
        ['678', 'Supplier Name', 'PasS'],
    ]
