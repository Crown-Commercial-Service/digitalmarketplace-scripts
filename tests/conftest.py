# -*- coding: utf-8 -*-
"""Config for py.test: Defining fixtures in here makes them available to test functions."""
import json
import os
import pytest
from mock import Mock


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.fixture
def mock_data_client():
    """Mock data client for use in tests. These can be overwritten in individual tests."""
    mock_data_client = Mock()
    mock_data_client.get_framework.return_value = dict(frameworks=dict(lots=[
        {'slug': 'test_lot_slug_1'},
        {'slug': 'test_lot_slug_2'},
    ]))
    mock_data_client.find_draft_services_iter.return_value = {}
    mock_data_client.export_users.return_value = {
        'users': [
            {'supplier_id': 12345, 'application_status': 'application', 'extraneous_field': 'foo'},
            {'supplier_id': 23456, 'application_status': 'no_application', 'extraneous_field': 'foo'},
            {'supplier_id': 123, 'application_status': 'application', 'extraneous_field': 'foo'},
            {'supplier_id': 456, 'application_status': 'application', 'extraneous_field': 'foo'},
            {'supplier_id': 789, 'application_status': 'no_application', 'extraneous_field': 'foo'},
            {'supplier_id': 101, 'application_status': 'no_application', 'extraneous_field': 'foo'}
        ]
    }

    with open(os.path.join(FIXTURES_DIR, 'test_supplier_frameworks_response.json')) as supplier_frameworks_response:
        mock_data_client.find_framework_suppliers.return_value = json.loads(supplier_frameworks_response.read())
    return mock_data_client
