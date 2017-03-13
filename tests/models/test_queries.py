import mock
import pytest

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
    csv_reader.side_effect = [
        DataFrame([{'id': 1, 'val': 'one'}, {'id': 2, 'val': 'two'}, {'id': 3, 'val': 'three'}]),
        DataFrame([{'fk': 1, 'col': 100}, {'fk': 1, 'col': 200}, {'fk': 3, 'col': 300}])
    ]

    assert queries.join(
        ({'model': '1', 'key': 'id'}, {'model': '2', 'key': 'fk'}), 'data'
    ).values.tolist() == [
        [1, 'one', 100.0, 1],
        [1, 'one', 200.0, 1],
        [3, 'three', 300.0, 3],
    ]


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
