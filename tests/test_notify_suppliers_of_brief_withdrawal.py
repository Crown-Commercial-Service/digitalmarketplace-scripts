import mock
from datetime import date

from dmscripts import notify_suppliers_of_brief_withdrawal as tested_script


WITHDRAWN_BRIEFS = (
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
)


BRIEF_RESPONSES = (
    {"id": 4321, "respondToEmailAddress": "email@me.now"},
    {"id": 4389, "respondToEmailAddress": "email@them.now"}
)


EXPECTED_BRIEF_CONTEXT = {
    'brief_title': "Tea Drinker",
    'brief_link': 'https://www.preview.marketplace.team/digital-outcomes-and-specialists/opportunities/123'
}


@mock.patch('dmapiclient.DataAPIClient', autospec=True)
def test_get_brief_response_emails(data_api_client):
    data_api_client.find_brief_responses_iter.return_value = BRIEF_RESPONSES
    assert tested_script.get_brief_response_emails(data_api_client, {"id": 1234}) == ["email@me.now", "email@them.now"]


def test_create_context_for_brief():
    assert tested_script.create_context_for_brief('preview', WITHDRAWN_BRIEFS[0]) == EXPECTED_BRIEF_CONTEXT


@mock.patch('dmutils.email.DMNotifyClient', autospec=True)
@mock.patch('dmscripts.notify_suppliers_of_brief_withdrawal.create_context_for_brief')
@mock.patch('dmscripts.notify_suppliers_of_brief_withdrawal.get_brief_response_emails')
@mock.patch('dmapiclient.DataAPIClient', autospec=True)
def test_main_calls_correct_script_methods(
    data_api_client,
    get_brief_response_emails,
    create_context_for_brief,
    notify_client,
):
    data_api_client.find_briefs_iter.return_value = WITHDRAWN_BRIEFS
    tested_script.create_context_for_brief.return_value = EXPECTED_BRIEF_CONTEXT
    get_brief_response_emails.side_effect = [["email@me.now", "email@them.now"], []]
    withdrawn_date = date(2016, 1, 28)
    tested_script.main(data_api_client, notify_client, "notify_template_id", "preview", mock.Mock(), withdrawn_date)
    expected_call_args = [mock.call(status='withdrawn', withdrawn_on=withdrawn_date)]
    assert get_brief_response_emails.call_args_list == [
        mock.call(data_api_client, 123),
        mock.call(data_api_client, 235),
    ]
    assert data_api_client.find_briefs_iter.call_args_list == expected_call_args
    assert create_context_for_brief.call_args_list == [mock.call("preview", WITHDRAWN_BRIEFS[0])]
    assert notify_client.send_email.call_args_list == [
        mock.call("email@me.now", "notify_template_id", EXPECTED_BRIEF_CONTEXT, allow_resend=False),
        mock.call("email@them.now", "notify_template_id", EXPECTED_BRIEF_CONTEXT, allow_resend=False)
    ]


@mock.patch('dmutils.email.DMNotifyClient', autospec=True)
@mock.patch('dmapiclient.DataAPIClient', autospec=True)
def test_main_calls_correct_external_client_methods(data_api_client, notify_client):

    data_api_client.find_briefs_iter.return_value = WITHDRAWN_BRIEFS
    data_api_client.find_brief_responses_iter.side_effect = (BRIEF_RESPONSES, [])
    withdrawn_date = date.today()

    result = tested_script.main(
        data_api_client, notify_client, 'notify_template_id', 'preview', mock.Mock(), withdrawn_date
    )

    assert result is True
    expected_call_args = [mock.call(status='withdrawn', withdrawn_on=withdrawn_date)]
    assert data_api_client.find_briefs_iter.call_args_list == expected_call_args
    assert notify_client.send_email.call_args_list == [
        mock.call("email@me.now", "notify_template_id", EXPECTED_BRIEF_CONTEXT, allow_resend=False),
        mock.call("email@them.now", "notify_template_id", EXPECTED_BRIEF_CONTEXT, allow_resend=False)
    ]


@mock.patch('dmutils.email.DMNotifyClient', autospec=True)
@mock.patch('dmapiclient.DataAPIClient', autospec=True)
def test_single_call_when_brief_id_specified(data_api_client, notify_client):
    """Script should only look up brief responses for given brief id when brief id is specified."""
    data_api_client.find_briefs_iter.return_value = WITHDRAWN_BRIEFS
    brief_id = 235
    result = tested_script.main(
        data_api_client, notify_client, 'notify_template_id', 'preview', mock.Mock(), date.today(), brief_id=brief_id
    )

    assert result is True
    data_api_client.find_brief_responses_iter.assert_called_once_with(brief_id=brief_id, status='submitted')
