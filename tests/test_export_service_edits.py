from dmapiclient import DataAPIClient
from unittest import mock

from dmscripts.export_service_edits import diff_archived_services, service_edit_diff


class TestArchivedServiceDiff:
    def test_no_content(self):
        new_service = {"frameworkFamily": "foo", "lot": "bar"}
        old_service = {"frameworkFamily": "foo", "lot": "bar"}

        assert diff_archived_services(old_service, new_service) == ""

    def test_diff_string_change(self):
        new_service = {"frameworkFamily": "foo", "lot": "bar", "key": "new value"}
        old_service = {"frameworkFamily": "foo", "lot": "bar", "key": "value"}

        assert diff_archived_services(old_service, new_service) == """key:
- value
+ new value
? ++++
"""


class TestServiceEditDiff:
    def test_diff(self):
        data_api_client = mock.Mock(autospec=DataAPIClient)
        data_api_client.get_archived_service.side_effect = [
            {"frameworkFamily": "foo", "lot": "bar", "key": "new value"},
            {"frameworkFamily": "foo", "lot": "bar", "key": "value"},
        ]

        audit_event = {
            "type": "update_service",
            "data": {"newArchivedServiceId": 1, "oldArchivedServiceId": 2}
        }
        assert service_edit_diff(data_api_client, audit_event) == """key:
- value
+ new value
? ++++
"""
        data_api_client.assert_has_calls([mock.call.get_archived_service(1), mock.call.get_archived_service(2)])
