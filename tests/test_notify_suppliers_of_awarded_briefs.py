import mock

from freezegun import freeze_time

from dmscripts import notify_suppliers_of_awarded_briefs as tested_script


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

CANCELLED_BRIEFS = [
    {
        "framework": {
            "family": "digital-outcomes-and-specialists",
            "slug": "digital-outcomes-and-specialists-2",
        },
        "id": 333,
        "status": "cancelled",
        "title": "Biscuit Dunker",
        "cancelledAt": "2018-01-01T15:07:07.946308Z"
    }
]

UNSUCCESSFUL_BRIEFS = [
    {
        "framework": {
            "family": "digital-outcomes-and-specialists",
            "slug": "digital-outcomes-and-specialists-2",
        },
        "id": 555,
        "status": "unsuccessful",
        "title": "Coffee Grinder",
        "unsuccessfulAt": "2018-01-01T15:07:07.946308Z"
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


@mock.patch('dmscripts.notify_suppliers_of_awarded_briefs._create_context_for_brief')
@mock.patch('dmapiclient.DataAPIClient', autospec=True)
def test_main_calls_correct_methods(data_api_client, create_context_for_brief):
    data_api_client.find_brief_responses_iter.side_effect = [
        [   # Awarded brief responses for each awarded brief
            _get_dummy_brief_response(4321, AWARDED_BRIEFS[0], awarded=True),
            _get_dummy_brief_response(4322, AWARDED_BRIEFS[1], awarded=True),
        ],
        [   # 'Losing' brief responses for the first awarded brief
            _get_dummy_brief_response(4322, AWARDED_BRIEFS[0]),
            _get_dummy_brief_response(4323, AWARDED_BRIEFS[0], valid_email=False),
        ],
        [   # No 'losing' brief responses for the 2nd awarded brief
        ],
        [   # One brief response for the cancelled brief
            _get_dummy_brief_response(4325, CANCELLED_BRIEFS[0]),
        ],
        [   # One brief response for the unsuccessful brief
            _get_dummy_brief_response(4326, UNSUCCESSFUL_BRIEFS[0]),
        ],
    ]
    data_api_client.find_briefs_iter.side_effect = [
        CANCELLED_BRIEFS, UNSUCCESSFUL_BRIEFS
    ]
    tested_script._create_context_for_brief.return_value = EXPECTED_BRIEF_CONTEXT

    with freeze_time('2018-01-02'):
        notifications = list(tested_script.main("notify_template_id", "preview", data_api_client=data_api_client))

    assert data_api_client.find_brief_responses_iter.call_args_list == [
        mock.call(awarded_at="2018-01-01"),
        mock.call(brief_id=123, status='submitted'),
        mock.call(brief_id=456, status='submitted'),
        mock.call(brief_id=333),
        mock.call(brief_id=555)
    ]
    assert create_context_for_brief.call_args_list == [
        mock.call("preview", AWARDED_BRIEFS[0]),
        mock.call("preview", AWARDED_BRIEFS[0]),
        mock.call("preview", AWARDED_BRIEFS[1]),
        mock.call("preview", CANCELLED_BRIEFS[0]),
        mock.call("preview", UNSUCCESSFUL_BRIEFS[0])
    ]
    # Only email if a valid email address is present
    assert notifications == [
        {
            "email_address": "lucky_winner_4321@example.com",
            "template_id": "notify_template_id",
            "personalisation": EXPECTED_BRIEF_CONTEXT
        },
        {
            "email_address": "sore_loser_4322@example.com",
            "template_id": "notify_template_id",
            "personalisation": EXPECTED_BRIEF_CONTEXT
        },
        {
            "email_address": "lucky_winner_4322@example.com",
            "template_id": "notify_template_id",
            "personalisation": EXPECTED_BRIEF_CONTEXT
        },
        {
            "email_address": "sore_loser_4325@example.com",
            "template_id": "notify_template_id",
            "personalisation": EXPECTED_BRIEF_CONTEXT
        },
        {
            "email_address": "sore_loser_4326@example.com",
            "template_id": "notify_template_id",
            "personalisation": EXPECTED_BRIEF_CONTEXT
        }
    ]
    # Single BriefResponse API request not called
    assert data_api_client.get_brief_response.called is False


@mock.patch('dmapiclient.DataAPIClient', autospec=True)
def test_main_calls_get_brief_response_when_brief_response_ids_specified(data_api_client):
    """Script should only look up brief responses for a given list of ids if they are specified."""
    data_api_client.get_brief_response.side_effect = [
        {'briefResponses': _get_dummy_brief_response(4321, AWARDED_BRIEFS[0], awarded=True)},
        {'briefResponses': _get_dummy_brief_response(4322, AWARDED_BRIEFS[0])}
    ]

    with freeze_time('2018-01-02'):
        notifications = list(tested_script.main(
            'notify_template_id', 'preview',
            brief_response_ids=[4321, 4322], data_api_client=data_api_client,
        ))

    assert data_api_client.get_brief_response.call_args_list == [
        mock.call(4321),
        mock.call(4322)
    ]
    assert notifications == [
        {
            "email_address": "lucky_winner_4321@example.com",
            "template_id": "notify_template_id",
            "personalisation": EXPECTED_BRIEF_CONTEXT
        },
        {
            "email_address": "sore_loser_4322@example.com",
            "template_id": "notify_template_id",
            "personalisation": EXPECTED_BRIEF_CONTEXT
        }
    ]


@mock.patch('dmapiclient.DataAPIClient', autospec=True)
def test_main_uses_awarded_at_date_param_if_provided(data_api_client):
    data_api_client.find_brief_responses_iter.side_effect = [
        [   # Awarded brief response for the awarded brief
            _get_dummy_brief_response(4321, AWARDED_BRIEFS[0], awarded=True),
        ],
        [
            # No 'losing' brief responses for the awarded brief
        ],
        [   # Brief response for a cancelled brief
            _get_dummy_brief_response(4321, CANCELLED_BRIEFS[0])
        ],
        [   # Brief response for an unsuccessful brief
            _get_dummy_brief_response(4321, UNSUCCESSFUL_BRIEFS[0])
        ]
    ]
    data_api_client.find_briefs_iter.side_effect = [
        CANCELLED_BRIEFS, UNSUCCESSFUL_BRIEFS
    ]

    with freeze_time('2018-02-02'):
        assert list(tested_script.main(
            notify_template_id="notify_template_id",
            stage="preview",
            awarded_at="2018-01-01",
            data_api_client=data_api_client
        ))

    assert data_api_client.find_brief_responses_iter.call_args_list == [
        mock.call(awarded_at="2018-01-01"),
        mock.call(brief_id=123, status="submitted"),
        mock.call(brief_id=333),
        mock.call(brief_id=555)
    ]
