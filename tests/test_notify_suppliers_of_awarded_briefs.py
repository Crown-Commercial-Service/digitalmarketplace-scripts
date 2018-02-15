import mock

from freezegun import freeze_time

from dmscripts import notify_suppliers_of_awarded_briefs as tested_script
from dmutils.email.exceptions import EmailError
from dmutils.email.helpers import hash_string


AWARDED_BRIEFS = [
    {
        "framework": {
            "family": "digital-outcomes-and-specialists",
            "slug": "digital-outcomes-and-specialists-2",
        },
        "id": 123,
        "status": "awarded",
        "title": "Tea Drinker"
    },
    {
        "framework": {
            "family": "digital-outcomes-and-specialists",
            "slug": "digital-outcomes-and-specialists-2",
        },
        "id": 456,
        "status": "awarded",
        "title": "Cookie Muncher"
    }
]


EXPECTED_BRIEF_CONTEXT = {
    'brief_title': "Tea Drinker",
    'brief_link': 'https://www.preview.marketplace.team/digital-outcomes-and-specialists/opportunities/123',
    'utm_date': "20180102"
}


def _get_dummy_brief_response(id_, brief, awarded=False, valid_email=True):
    brief_response = {
        "awardedAt": '2018-01-01T23:59:59.999999Z',
        "briefId": brief['id'],
        "brief": brief,
        "id": id_,
        "respondToEmailAddress": "sore_loser_{}@example.com".format(id_),
    }
    if awarded:
        brief_response['awardedAt'] = '2018-01-01T23:59:59.999999Z'
        brief_response['status'] = 'awarded'
        brief_response["respondToEmailAddress"] = "lucky_winner_{}@example.com".format(id_)
    if not valid_email:
        brief_response['respondToEmailAddress'] = ""
    return brief_response


def test_create_context_for_brief():
    with freeze_time('2018-01-02'):
        assert tested_script._create_context_for_brief('preview', AWARDED_BRIEFS[0]) == EXPECTED_BRIEF_CONTEXT


@mock.patch('dmutils.email.DMNotifyClient', autospec=True)
@mock.patch('dmscripts.notify_suppliers_of_awarded_briefs._create_context_for_brief')
@mock.patch('dmapiclient.DataAPIClient', autospec=True)
def test_main_calls_correct_methods(data_api_client, create_context_for_brief, notify_client):
    data_api_client.find_brief_responses_iter.side_effect = [
        [   # Only get awarded BRs on the first call
            _get_dummy_brief_response(4321, AWARDED_BRIEFS[0], awarded=True),
            _get_dummy_brief_response(4322, AWARDED_BRIEFS[1], awarded=True),
        ],
        [   # Get submitted BRs for 1st awarded brief on the second call
            _get_dummy_brief_response(4322, AWARDED_BRIEFS[0]),
            _get_dummy_brief_response(4323, AWARDED_BRIEFS[0], valid_email=False),
        ],
        [   # No submitted BRs for the 2nd awarded brief
        ]
    ]
    tested_script._create_context_for_brief.return_value = EXPECTED_BRIEF_CONTEXT

    with freeze_time('2018-01-02'):
        assert tested_script.main(data_api_client, notify_client, "notify_template_id", "preview", mock.Mock())

    assert data_api_client.find_brief_responses_iter.call_args_list == [
        mock.call(awarded_at="2018-01-01"),
        mock.call(brief_id=123, status='submitted'),
        mock.call(brief_id=456, status='submitted')
    ]
    assert create_context_for_brief.call_args_list == [
        mock.call("preview", AWARDED_BRIEFS[0]),
        mock.call("preview", AWARDED_BRIEFS[0]),
        mock.call("preview", AWARDED_BRIEFS[1])
    ]
    # Only email if a valid email address is present
    assert notify_client.send_email.call_args_list == [
        mock.call(
            "lucky_winner_4321@example.com", "notify_template_id", EXPECTED_BRIEF_CONTEXT, allow_resend=False
        ),
        mock.call(
            "sore_loser_4322@example.com", "notify_template_id", EXPECTED_BRIEF_CONTEXT, allow_resend=False
        ),
        mock.call(
            "lucky_winner_4322@example.com", "notify_template_id", EXPECTED_BRIEF_CONTEXT, allow_resend=False
        )
    ]
    # Single BriefResponse API request not called
    assert data_api_client.get_brief_response.called is False


@mock.patch('dmutils.email.DMNotifyClient', autospec=True)
@mock.patch('dmapiclient.DataAPIClient', autospec=True)
def test_main_calls_get_brief_response_when_brief_response_ids_specified(data_api_client, notify_client):
    """Script should only look up brief responses for a given list of ids if they are specified."""
    data_api_client.get_brief_response.side_effect = [
        {'briefResponses': _get_dummy_brief_response(4321, AWARDED_BRIEFS[0], awarded=True)},
        {'briefResponses': _get_dummy_brief_response(4322, AWARDED_BRIEFS[0])}
    ]

    with freeze_time('2018-01-02'):
        assert tested_script.main(
            data_api_client, notify_client, 'notify_template_id', 'preview', mock.Mock(),
            brief_response_ids=[4321, 4322]
        )

    assert data_api_client.get_brief_response.call_args_list == [
        mock.call(4321),
        mock.call(4322)
    ]
    assert notify_client.send_email.call_args_list == [
        mock.call(
            "lucky_winner_4321@example.com", "notify_template_id", EXPECTED_BRIEF_CONTEXT, allow_resend=False
        ),
        mock.call(
            "sore_loser_4322@example.com", "notify_template_id", EXPECTED_BRIEF_CONTEXT, allow_resend=False
        )
    ]


@mock.patch('dmutils.email.DMNotifyClient', autospec=True)
@mock.patch('dmapiclient.DataAPIClient', autospec=True)
def test_main_uses_awarded_at_date_param_if_provided(data_api_client, notify_client):
    data_api_client.find_brief_responses_iter.return_value = [
        _get_dummy_brief_response(4321, AWARDED_BRIEFS[0], awarded=True)
    ]

    with freeze_time('2018-02-02'):
        assert tested_script.main(
            data_api_client, notify_client, "notify_template_id", "preview", mock.Mock(), awarded_at="2018-01-01"
        )

    assert data_api_client.find_brief_responses_iter.call_args_list == [
        mock.call(awarded_at="2018-01-01"),
        mock.call(brief_id=123, status="submitted")
    ]


@mock.patch('dmutils.email.DMNotifyClient', autospec=True)
@mock.patch('dmapiclient.DataAPIClient', autospec=True)
def test_main_catches_email_errors_and_returns_ids(data_api_client, notify_client):
    logger = mock.Mock()
    notify_client.send_email.side_effect = [EmailError, True]
    data_api_client.find_brief_responses_iter.side_effect = [
        [_get_dummy_brief_response(4321, AWARDED_BRIEFS[0], awarded=True)],
        [_get_dummy_brief_response(1234, AWARDED_BRIEFS[0], awarded=False)],
    ]

    assert not tested_script.main(
        data_api_client, notify_client, 'notify_template_id', 'preview', logger
    )

    assert logger.error.call_args_list == [
        mock.call(
            'Email sending failed for BriefResponse {brief_response_id} (Brief ID {brief_id})',
            extra={
                "brief_id": 123,
                "brief_response_id": 4321
            }
        ),
        mock.call(
            "Email sending failed for the following {count} BriefResponses: {brief_response_ids}",
            extra={
                'brief_response_ids': '4321',
                'count': 1
            }
        )
    ]
    assert logger.info.call_args_list == [
        mock.call(
            "{dry_run}EMAIL: Award of Brief Response ID: {brief_response_id} to {email_address}",
            extra={
                'dry_run': '',
                'brief_response_id': 1234,
                'email_address': hash_string('sore_loser_1234@example.com'),
            }
        )
    ]
