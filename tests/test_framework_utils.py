from dmapiclient import HTTPError

from dmscripts.helpers.framework_helpers import (
    get_submitted_drafts, has_supplier_submitted_services, set_framework_result
)


def test_get_submitted_drafts_calls_with_correct_arguments(mock_data_client):
    mock_data_client.find_draft_services_iter.return_value = iter([])
    get_submitted_drafts(mock_data_client, 'digital-biscuits-and-cakes', 12345)
    mock_data_client.find_draft_services_iter.assert_called_with(12345, framework='digital-biscuits-and-cakes')


def test_get_submitted_drafts_returns_submitted_draft_services_only(mock_data_client):
    mock_data_client.find_draft_services_iter.return_value = iter((
        {"id": 1, "status": "not-submitted"},
        {"id": 2, "status": "submitted"},
    ))
    result = get_submitted_drafts(mock_data_client, 12345, 'digital-biscuits-and-cakes')
    assert (result == [{"id": 2, "status": "submitted"}])


def test_get_submitted_drafts_returns_submitted_draft_services_without_service_ids_only(mock_data_client):
    mock_data_client.find_draft_services_iter.return_value = iter((
        {"id": 1, "status": "not-submitted"},
        {"id": 2, "status": "submitted", "serviceId": "ALREADY_A_LIVE_SERVICE"},
        {"id": 3, "status": "submitted"},
    ))
    result = get_submitted_drafts(mock_data_client, 12345, 'digital-biscuits-and-cakes')
    assert (result == [{"id": 3, "status": "submitted"}])


def test_set_framework_result_calls_with_correct_arguments(mock_data_client):
    assert set_framework_result(mock_data_client, 'g-whizz-6', 123456, True, 'user') == \
        '  Result set OK: 123456 - PASS'
    mock_data_client.set_framework_result.assert_called_with(123456, 'g-whizz-6', True, 'user')


def test_set_framework_result_returns_error_message_if_update_fails(mock_data_client):
    mock_data_client.set_framework_result.side_effect = HTTPError()
    assert set_framework_result(mock_data_client, 'g-whizz-6', 123456, True, 'user') == \
        '  Error inserting result for 123456 (True): Request failed (status: 503)'


def test_has_supplier_submitted_services_for_some_services(mock_data_client):
    mock_data_client.find_draft_services_iter.return_value = iter((
        {"status": "submitted"},
        {"status": "submitted"},
    ))
    assert has_supplier_submitted_services(mock_data_client, 'g-spot-7', 12345) is True


def test_has_supplier_submitted_services_for_no_services(mock_data_client):
    mock_data_client.find_draft_services_iter.return_value = iter(({"status": "not-submitted"},))
    assert has_supplier_submitted_services(mock_data_client, 'g-spot-7', 12345) is False
