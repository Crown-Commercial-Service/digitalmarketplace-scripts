import mock
from freezegun import freeze_time
import datetime
import pytest
from datetime import datetime, date, timedelta

from dmutils.email import EmailError
from dmscripts import notify_suppliers_about_withdrawn_briefs as tested_script


class TestMain:

    @mock.patch('dmscripts.notify_suppliers_about_withdrawn_briefs.data_api_client')
    def test_get_brief_responses(self, data_api_client):
        data_api_client.find_brief_responses.return_value = {"briefResponses": [{"id": 4321}, {"id": 4389}]}
        assert tested_script.get_brief_responses(data_api_client, {"id": 1234}) == [{"id": 4321}, {"id": 4389}]

    @mock.patch('dmscripts.notify_suppliers_about_withdrawn_briefs.get_brief_responses')
    def test_get_withdrawn_briefs_with_responses(self, get_brief_responses):
        get_brief_responses.side_effect = [
            [{"id": 4321}, {"id": 4389}],
            [],
        ]
        briefs = [
            {"id": 123, "withdrawnAt": "2016-01-28 16:23:50.618053"},
            {"id": 235, "withdrawnAt": "2016-01-28 08:23:50.618053"}
        ]
        briefs_with_responses = {123: [{"id": 4321}, {"id": 4389}], 235: []}
        assert tested_script.get_withdrawn_briefs_with_responses(mock.Mock(), briefs) == briefs_with_responses

    @mock.patch('dmscripts.notify_suppliers_about_withdrawn_briefs.get_withdrawn_briefs_with_responses')
    @mock.patch('dmscripts.notify_suppliers_about_withdrawn_briefs.data_api_client')
    def test_main_calls_functions(self, data_api_client, get_withdrawn_briefs_with_responses):
        withdrawn_briefs = [
            {"id": 123, "withdrawnAt": "2016-01-28 16:23:50.618053"},
            {"id": 235, "withdrawnAt": "2016-01-28 08:23:50.618053"}
        ]
        data_api_client.find_briefs.return_value = {"briefs": withdrawn_briefs}
        get_withdrawn_briefs_with_responses.return_value = {123: [{"id": 4321}, {"id": 4389}], 235: []}
        with freeze_time('2016-01-29 03:04:05'):
            tested_script.main(data_api_client)
            yesterday = date(2016, 1, 28)
            expected_args = [mock.call(withdrawn_on=yesterday)]
            assert data_api_client.find_briefs.call_args_list == expected_args
            assert tested_script.get_withdrawn_briefs_with_responses.call_args_list == [mock.call(
                data_api_client, withdrawn_briefs
            )]
