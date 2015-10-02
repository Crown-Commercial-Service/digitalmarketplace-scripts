try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import pytest
import mock

from dmutils.apiclient import HTTPError

from dmscripts.generate_user_email_list import (
    selection_status, is_registered_with_framework, find_supplier_users, list_users
)


@pytest.fixture
def mock_data_client():
    return mock.Mock()


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
    mock_data_client.get_selection_answers.return_value = {
        'selectionAnswers': {'questionAnswers': {'status': 'complete'}}}

    assert selection_status(mock_data_client, 'g-cloud-7')(user)[0] == 'complete'


def test_selection_status_no_answers(mock_data_client, user):
    mock_data_client.get_selection_answers.side_effect = HTTPError(mock.Mock(status_code=404))

    assert selection_status(mock_data_client, 'g-cloud-7')(user)[0] == 'unstarted'


def test_selection_status_http_error(mock_data_client, user):
    mock_data_client.get_selection_answers.side_effect = HTTPError(mock.Mock(status_code=503))

    assert selection_status(mock_data_client, 'g-cloud-7')(user)[0] == 'error-503'


def test_selection_status_no_status(mock_data_client, user):
    mock_data_client.get_selection_answers.return_value = {'invalid': 'response'}
    user = {'supplier': {'supplierId': 1234}}

    assert selection_status(mock_data_client, 'g-cloud-7')(user)[0] == 'error-key-error'


def test_is_registered_with_framework(mock_data_client, user):
    mock_data_client.find_audit_events.return_value = {
        'auditEvents': [
            {'data': {'frameworkSlug': 'g-cloud-7'}},
            {'data': {'frameworkSlug': 'g-cloud-6'}},
        ]
    }

    is_registered = is_registered_with_framework(mock_data_client, 'g-cloud-7')

    assert is_registered(user)[0]


def test_is_not_registered_with_framework(mock_data_client, user):
    mock_data_client.find_audit_events.return_value = {
        'auditEvents': [
            {'data': {'frameworkSlug': 'g-cloud-5'}},
            {'data': {'frameworkSlug': 'g-cloud-6'}},
        ]
    }

    is_registered = is_registered_with_framework(mock_data_client, 'g-cloud-7')

    assert not is_registered(user)[0]


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
    mock_data_client.get_selection_answers.return_value = {
        'selectionAnswers': {'questionAnswers': {'status': 'complete'}}}
    mock_data_client.find_audit_events.return_value = {
        'auditEvents': [{'data': {'frameworkSlug': framework_slug}}]}

    list_users(mock_data_client, output, framework_slug, True)

    assert output.getvalue() == "complete,jane@example.com,Jane Example,1234,Examples Ltd.\r\n"


def test_list_users_without_status(mock_data_client):
    output = StringIO()
    framework_slug = 'g-cloud-7'

    mock_data_client.find_users_iter.return_value = [
        user(),
    ]
    mock_data_client.find_audit_events.return_value = {
        'auditEvents': [{'data': {'frameworkSlug': framework_slug}}]}

    list_users(mock_data_client, output, framework_slug, False)

    assert output.getvalue() == "jane@example.com,Jane Example,1234,Examples Ltd.\r\n"
