import pytest
import copy
from dmscripts.models.utils import process_collection, return_filtered_collection, return_sorted_collection


COLLECTION = (
    {"id": 1, "name": "Don"},
    {"id": 3, "name": "Peggy"},
    {"id": 5, "name": "Pete"},
    {"id": 2, "name": "Betty"},
    {"id": 4, "name": "Roger"},
    {"id": 6, "name": "Joan"}
)

# process_collection tests


def test_process_collection():
    rules = {'id': lambda x: int(x) * 10}
    processed_collection = copy.deepcopy(COLLECTION)
    process_collection(rules, processed_collection)

    assert (10, 30, 50, 20, 40, 60) == tuple((i['id'] for i in processed_collection))


def test_process_collection_if_rules_are_none():
    processed_collection = copy.deepcopy(COLLECTION)
    process_collection({}, processed_collection)

    assert COLLECTION == processed_collection

# return_filtered_collection tests


def test_return_filtered_collection():
    rules = [('id', '>', 3)]
    filtered_collection = return_filtered_collection(rules, COLLECTION)

    # remove numbers less than 4 from sequence: 1,3,5,2,4,6
    assert (5, 4, 6) == tuple((i['id'] for i in filtered_collection))


def test_return_filtered_collection_if_rules_are_none():
    assert COLLECTION == return_filtered_collection(None, COLLECTION)


def test_return_filtered_collection_if_operator_invalid():
    rules = [('id', 'contains', 3)]
    with pytest.raises(KeyError) as excinfo:
        filtered_collection = return_filtered_collection(rules, COLLECTION)

    assert 'contains' in str(excinfo.value)

# return_sorted_collection tests


def test_return_sorted_collection_by_ints():
    sorted_collection = return_sorted_collection('id', COLLECTION)
    assert (1, 2, 3, 4, 5, 6) == tuple((i['id'] for i in sorted_collection))


def test_return_sorted_collection_by_strings():
    sorted_collection = return_sorted_collection('name', COLLECTION)
    assert (
        'Betty', 'Don', 'Joan', 'Peggy', 'Pete', 'Roger'
    ) == tuple((i['name'] for i in sorted_collection))


def test_return_sorted_collection_if_key_is_none():
    assert COLLECTION == return_sorted_collection(None, COLLECTION)
