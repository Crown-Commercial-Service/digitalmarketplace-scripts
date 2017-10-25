import mock
from freezegun import freeze_time
import datetime
import pytest
from datetime import datetime, date, timedelta

from dmutils.email import EmailError
from dmscripts import notify_suppliers_about_withdrawn_briefs as tested_script


WITHDRAWN_BRIEFS = {"briefs": [
    {
        "id": 123,
        "withdrawnAt": "2016-01-28 16:23:50.618053",
        "title": "Tea Drinker",
        "frameworkFramework": "digital-outcomes-and-specialists"
    },
    {
        "id": 235,
        "withdrawnAt": "2016-01-28 08:23:50.618053",
        "title": "Cookie Muncher",
        "frameworkFramework": "digital-outcomes-and-specialists"
    }
]}
BRIEF_RESPONSES = {"briefResponses": [
    {"id": 4321, "respondToEmailAddress": "email@me.now"},
    {"id": 4389, "respondToEmailAddress": "email@them.now"}
]}


class TestMain:


    @mock.patch('dmscripts.notify_suppliers_about_withdrawn_briefs.data_api_client')
    def test_get_brief_response_emails(self, data_api_client):
        data_api_client.find_brief_responses.return_value = BRIEF_RESPONSES
        assert tested_script.get_brief_response_emails(data_api_client, {"id": 1234}) == ["email@me.now", "email@them.now"]

    def test_create_context_for_brief(self):
        assert tested_script.create_context_for_brief('preview', WITHDRAWN_BRIEFS["briefs"][0]) == {
            'brief_title': "Tea Drinker",
            'brief_link': 'https://www.preview.marketplace.team/digital-outcomes-and-specialists/opportunities/123'  # noqa
        }

    @mock.patch('dmscripts.notify_suppliers_about_withdrawn_briefs.create_context_for_brief')
    @mock.patch('dmscripts.notify_suppliers_about_withdrawn_briefs.get_brief_response_emails')
    @mock.patch('dmscripts.notify_suppliers_about_withdrawn_briefs.data_api_client')
    def test_main(self, data_api_client, get_brief_response_emails, create_context_for_brief):
        data_api_client.find_briefs.return_value = WITHDRAWN_BRIEFS
        get_brief_response_emails.side_effect = [["email@me.now", "email@them.now"], []]
        with freeze_time('2016-01-29 03:04:05'):
            tested_script.main(data_api_client, "preview")
            yesterday = date(2016, 1, 28)
            expected_args = [mock.call(withdrawn_on=yesterday)]
            assert data_api_client.find_briefs.call_args_list == expected_args
            assert create_context_for_brief.call_args_list == [mock.call("preview", WITHDRAWN_BRIEFS["briefs"][0])]
