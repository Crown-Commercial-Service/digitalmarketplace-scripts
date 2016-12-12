try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import mock
import pytest

from dmapiclient import HTTPError

from dmscripts.generate_user_email_list_declarations import (
    selection_status, find_supplier_users, list_users
)


@pytest.fixture
def user():
    return {
        'id': '1',
        'emailAddress': 'jane@example.com',
        'name': 'Jane Example',
        'active': True,
        'role': 'supplier',
        'supplier': {
            'supplierId': 1234,
            'name': "Examples Ltd.",
        }
    }


def test_selection_status(mock_data_client, user):
    mock_data_client.get_supplier_declaration.return_value = {'declaration': {'status': 'complete'}}

    assert selection_status(mock_data_client, 'g-cloud-7')(user)[0] == 'complete'


def test_selection_status_no_answers(mock_data_client, user):
    mock_data_client.get_supplier_declaration.side_effect = HTTPError(mock.Mock(status_code=404))

    assert selection_status(mock_data_client, 'g-cloud-7')(user)[0] == 'unstarted'


def test_selection_status_http_error(mock_data_client, user):
    mock_data_client.get_supplier_declaration.side_effect = HTTPError(mock.Mock(status_code=503))

    assert selection_status(mock_data_client, 'g-cloud-7')(user)[0] == 'error-503'


def test_selection_status_no_status(mock_data_client, user):
    mock_data_client.get_supplier_declaration.return_value = {'invalid': 'response'}
    user = {'supplier': {'supplierId': 1234}}

    assert selection_status(mock_data_client, 'g-cloud-7')(user)[0] == 'error-key-error'


def test_find_supplier_users(mock_data_client):
    mock_data_client.find_users_iter.return_value = [
        {'id': '1', 'active': True, 'role': 'supplier'},
        {'id': '2', 'active': False, 'role': 'supplier'},
        {'id': '3', 'active': True, 'role': 'admin'},
    ]

    users = list(find_supplier_users(mock_data_client))

    assert len(users) == 1
    assert users[0]['id'] == '1'


def test_list_users_with_status(mock_data_client):
    output = StringIO()
    framework_slug = 'g-cloud-7'

    mock_data_client.find_users_iter.return_value = [
        user(),
    ]
    mock_data_client.get_supplier_declaration.return_value = {'declaration': {'status': 'complete'}}
    mock_data_client.get_interested_suppliers.return_value = {'interestedSuppliers': [1234]}

    list_users(mock_data_client, output, framework_slug, True)

    assert output.getvalue() == "complete,jane@example.com,Jane Example,1234,Examples Ltd.\r\n"


def test_list_users_without_status(mock_data_client):
    output = StringIO()
    framework_slug = 'g-cloud-7'

    mock_data_client.find_users_iter.return_value = [
        user(),
    ]
    mock_data_client.get_interested_suppliers.return_value = {'interestedSuppliers': [1234]}

    list_users(mock_data_client, output, framework_slug, False)

    assert output.getvalue() == "jane@example.com,Jane Example,1234,Examples Ltd.\r\n"
