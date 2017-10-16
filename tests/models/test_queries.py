import mock
import pytest
from collections import OrderedDict

from pandas import DataFrame
from dmscripts.models import queries


@pytest.fixture
def csv_reader(request):
    pandas_read_csv_patch = mock.patch('pandas.read_csv')
    read_csv_mock = pandas_read_csv_patch.start()
    request.addfinalizer(pandas_read_csv_patch.stop)

    return read_csv_mock


def test_model(csv_reader):
    csv_reader.return_value = DataFrame([1, 2])

    assert queries.model('example', 'data').values.tolist() == [[1], [2]]


def test_join(csv_reader):
    left_data = DataFrame([
        {'fk': 1, 'col': 100},
        {'fk': 1, 'col': 200},
        {'fk': 3, 'col': 300}
    ])
    right_data = DataFrame([
        {'id': 1, 'val': 'one'},
        {'id': 2, 'val': 'two'},
        {'id': 3, 'val': 'three'}
    ])
    config_value = {'model_name': 'n', 'left_on': 'fk', 'right_on': 'id'}
    expected_result = [
        [100, 1, 1, 'one'],
        [200, 1, 1, 'one'],
        [300, 3, 3, 'three']
    ]

    csv_reader.return_value = right_data

    assert queries.join(left_data, directory='data', **config_value).values.tolist() == expected_result


def test_filter_rows():
    assert queries.filter_rows('val > 5 and val < 10', DataFrame([
        {'id': 1, 'val': 7},
        {'id': 2, 'val': 9},
        {'id': 3, 'val': 1},
        {'id': 4, 'val': 8},
        {'id': 5, 'val': 11},
    ])).values.tolist() == [
        [1, 7],
        [2, 9],
        [4, 8],
    ]


def test_process_fields():
    assert queries.process_fields({'val2': sum, 'val1': lambda x: x - 5}, DataFrame([
        {'id': 1, 'val1': 7, 'val2': [1, 2, 3]},
        {'id': 2, 'val1': 11, 'val2': [2, 3, 4]},
    ])).values.tolist() == [
        [1, 2, 6],
        [2, 6, 9],
    ]


def test_sort_by():
    assert queries.sort_by('val', DataFrame([
        {'id': 1, 'val': 7},
        {'id': 2, 'val': 9},
        {'id': 4, 'val': 8},
    ])).values.tolist() == [
        [1, 7],
        [4, 8],
        [2, 9],
    ]


def test_rename_fields():
    data = queries.rename_fields({'old key': 'new key'}, DataFrame([
        {'id': 1, 'old key': 7},
        {'id': 2, 'old key': 9},
        {'id': 4, 'old key': 8},
    ]))

    assert data.axes[1].tolist() == [u'id', u'new key']
    assert data.values.tolist() == [
        [1, 7],
        [2, 9],
        [4, 8]
    ]


def test_add_counts(csv_reader):
    csv_reader.return_value = DataFrame([
        {'fk': 1, 'status': True},
        {'fk': 1, 'status': True},
        {'fk': 1, 'status': False},
        {'fk': 2, 'status': False},
        {'fk': 2, 'status': False},
    ])

    data = queries.add_counts(('id', 'fk'), 'status', 'example', DataFrame([
        {'id': 1, 'val': 'one'},
        {'id': 2, 'val': 'two'},
        {'id': 3, 'val': 'three'}
    ]), 'data')

    assert data.axes[1].tolist() == [u'id', u'val', u'status-False', u'status-True']
    assert data.values.tolist() == [
        [1, 'one', 1.0, 2.0],
        [2, 'two', 2.0, 0.0],
        [3, 'three', 0.0, 0.0]
    ]


def test_assign_json_subfields():
    """Test fields are attributed at data level by assign_json_subfields"""
    od1 = OrderedDict([('field1', '111'), ('field2', '222'), ('field3', '333')])
    od2 = OrderedDict([('field1', '444'), ('field2', '555'), ('field3', '{555: 666}')])
    od3 = OrderedDict([('field2', '777'), ('field3', '888')])

    data = DataFrame([
        {'id': 1, 'json_field': od1},
        {'id': 2, 'json_field': od2},
        {'id': 3, 'json_field': od3},
        {'id': 4, 'json_field': {'field2': '999'}},
        {'id': 5, 'json_field': {}},
    ])
    assert list(data.columns) == ['id', 'json_field']

    data = queries.assign_json_subfields('json_field', ['field1', 'field3'], data)

    assert list(data.columns) == ['id', 'json_field', 'field1', 'field3']
    assert data.values.tolist()[0] == [1, od1, '111', '333']
    assert data.values.tolist()[1] == [2, od2, '444', '{555: 666}']
    assert data.values.tolist()[2] == [3, od3, '', '888']
    assert data.values.tolist()[3] == [4, {'field2': '999'}, '', '']
    assert data.values.tolist()[4] == [5, {}, '', '']


def test_add_aggregation_counts():
    data = DataFrame([
        {'id': 1, 'fk': 1},
        {'id': 2, 'fk': 1},
        {'id': 3, 'fk': 1},
        {'id': 4, 'fk': 1},
        {'id': 5, 'fk': 1},
        {'id': 6, 'fk': 2},
        {'id': 7, 'fk': 2},
        {'id': 8, 'fk': 2},
        {'id': 9, 'fk': 2},
    ])
    config_value = {
        'group_by': 'fk',
        'join': ('fk', 'fk'),
        'count_name': 'a_name',
    }
    expected_result = [
        [1, 1, 5],
        [1, 2, 5],
        [1, 3, 5],
        [1, 4, 5],
        [1, 5, 5],
        [2, 6, 4],
        [2, 7, 4],
        [2, 8, 4],
        [2, 9, 4],
    ]

    data = queries.add_aggregation_counts(data, **config_value)
    assert data.values.tolist() == expected_result


def test_add_aggregation_counts_filter():
    data = DataFrame([
        {'id': 1, 'fk': 1, 'some_field': 'good'},
        {'id': 2, 'fk': 1, 'some_field': 'good'},
        {'id': 3, 'fk': 1, 'some_field': 'bad'},
        {'id': 4, 'fk': 1, 'some_field': 'bad'},
        {'id': 5, 'fk': 1, 'some_field': 'bad'},
        {'id': 6, 'fk': 2, 'some_field': 'good'},
        {'id': 7, 'fk': 2, 'some_field': 'good'},
        {'id': 8, 'fk': 2, 'some_field': 'good'},
        {'id': 9, 'fk': 2, 'some_field': 'bad'},
    ])
    config_value = {
        'group_by': 'fk',
        'join': ('fk', 'fk'),
        'count_name': 'a_name',
        'query': 'some_field == "good"',

    }
    expected_result = [
        [1, 1, 'good', 2],
        [1, 2, 'good', 2],
        [1, 3, 'bad', 2],
        [1, 4, 'bad', 2],
        [1, 5, 'bad', 2],
        [2, 6, 'good', 3],
        [2, 7, 'good', 3],
        [2, 8, 'good', 3],
        [2, 9, 'bad', 3]
    ]

    data = queries.add_aggregation_counts(data, **config_value)
    assert data.values.tolist() == expected_result


def test_drop_duplicates():
    data = DataFrame([
        OrderedDict([('id', 1), ('fk', 1)]),
        OrderedDict([('id', 1), ('fk', 2)]),
        OrderedDict([('id', 1), ('fk', 3)]),
        OrderedDict([('id', 2), ('fk', 2)]),
        OrderedDict([('id', 2), ('fk', 2)]),
        OrderedDict([('id', 2), ('fk', 3)]),
        OrderedDict([('id', 3), ('fk', 3)]),
        OrderedDict([('id', 3), ('fk', 3)]),
        OrderedDict([('id', 3), ('fk', 3)]),
    ])
    expected_result = [
        [1, 1],
        [1, 2],
        [1, 3],
        [2, 2],
        [2, 3],
        [3, 3],
    ]
    data = queries.drop_duplicates(data)
    assert data.values.tolist() == expected_result


def test_duplicate_fields():
    data = DataFrame([
        OrderedDict([('id', 1), ('fk', 1)]),
        OrderedDict([('id', 1), ('fk', 2)]),
        OrderedDict([('id', 1), ('fk', 3)]),
        OrderedDict([('id', 2), ('fk', 2)]),
        OrderedDict([('id', 2), ('fk', 2)]),
        OrderedDict([('id', 2), ('fk', 3)]),
        OrderedDict([('id', 3), ('fk', 3)]),
        OrderedDict([('id', 3), ('fk', 3)]),
        OrderedDict([('id', 3), ('fk', 3)]),
    ])
    expected_result = [
        [1, 1, 1],
        [1, 2, 1],
        [1, 3, 1],
        [2, 2, 2],
        [2, 2, 2],
        [2, 3, 2],
        [3, 3, 3],
        [3, 3, 3],
        [3, 3, 3],
    ]
    config_entry = ('id', 'duplicate_id')
    data = queries.duplicate_fields(data, *config_entry)
    assert list(data.columns) == ['id', 'fk', 'duplicate_id']
    assert data.values.tolist() == expected_result
