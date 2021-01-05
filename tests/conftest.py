# -*- coding: utf-8 -*-
"""Config for py.test: Defining fixtures in here makes them available to test functions."""
import json
import os
import pytest
from mock import Mock
import requests_mock

from dmtestutils.api_model_stubs import FrameworkStub, LotStub


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.fixture
def mock_data_client():
    """Mock data client for use in tests. These can be overwritten in individual tests."""
    mock_data_client = Mock()
    mock_data_client.get_framework.return_value = FrameworkStub(
        lots=[
            LotStub(slug="test_lot_slug_1").response(),
            LotStub(slug="test_lot_slug_2").response(),
        ],
    ).single_result_response()

    mock_data_client.find_draft_services_iter.return_value = {}
    mock_data_client.export_users.return_value = {
        "users": [
            {
                "supplier_id": 12345,
                "application_status": "application",
                "email address": "1@12345",
                "extraneous_field": "foo",
            },
            {
                "supplier_id": 23456,
                "application_status": "no_application",
                "email address": "1@23456",
                "extraneous_field": "foo",
            },
            {
                "supplier_id": 123,
                "application_status": "application",
                "email address": "1@123",
                "extraneous_field": "foo",
            },
            {
                "supplier_id": 456,
                "application_status": "application",
                "email address": "1@456",
                "extraneous_field": "foo",
            },
            {
                "supplier_id": 789,
                "application_status": "no_application",
                "email address": "1@789",
                "extraneous_field": "foo",
            },
            {
                "supplier_id": 101,
                "application_status": "no_application",
                "email address": "1@101",
                "extraneous_field": "foo",
            },
        ]
    }

    with open(
        os.path.join(FIXTURES_DIR, "test_supplier_frameworks_response.json")
    ) as supplier_frameworks_response:
        mock_data_client.find_framework_suppliers.return_value = json.loads(
            supplier_frameworks_response.read()
        )
        mock_data_client.find_framework_suppliers_iter.return_value = iter(
            mock_data_client.find_framework_suppliers.return_value["supplierFrameworks"]
        )
    return mock_data_client


@pytest.yield_fixture
def rmock():
    with requests_mock.mock() as rmock:
        real_register_uri = rmock.register_uri

        def register_uri_with_complete_qs(*args, **kwargs):
            if 'complete_qs' not in kwargs:
                kwargs['complete_qs'] = True

            return real_register_uri(*args, **kwargs)

        rmock.register_uri = register_uri_with_complete_qs

        yield rmock
