import mock
import pytest
from freezegun import freeze_time
from dmutils.email.exceptions import EmailError

from datetime import datetime

from dmscripts.notify_suppliers_of_new_questions_answers import (
    main,
    get_live_briefs_with_new_questions_and_answers_between_two_dates,
    get_ids_of_suppliers_who_started_or_finished_applying,
    get_ids_of_suppliers_who_asked_a_clarification_question,
    get_ids_of_interested_suppliers_for_briefs,
    get_supplier_email_addresses_by_supplier_id,
    invert_a_dictionary_so_supplier_id_is_key_and_brief_id_is_value,
    create_context_for_supplier,
    send_supplier_emails,
    get_template_personalisation,
)

NOTIFY_API_KEY = "1" * 73

ALL_BRIEFS = [
    # a brief with no questions
    {"id": 0, "clarificationQuestions": []},

    # a brief with a question outside of the date range
    {"id": 1, "clarificationQuestions": [{"publishedAt": "2017-03-22T06:00:00.669156Z"}]},

    # a brief with two questions outside of the date range
    {"id": 2, "clarificationQuestions": [
        {"publishedAt": "2017-03-21T06:00:00.669156Z"},
        {"publishedAt": "2017-03-22T06:00:00.669156Z"}
    ]},

    # a brief with a question inside of the date range
    {"id": 3, "clarificationQuestions": [
        {"publishedAt": "2017-03-23T06:00:00.669156Z"}
    ], 'title': 'Amazing Title', 'framework': {'family': 'digital-outcomes-and-specialists'}},

    # a brief with two questions inside of the date range
    {"id": 4, "clarificationQuestions": [
        {"publishedAt": "2017-03-22T18:00:00.669156Z"},
        {"publishedAt": "2017-03-23T06:00:00.669156Z"}
    ], 'title': 'Brilliant Title', 'framework': {'family': 'digital-outcomes-and-specialists'}},

    # a brief with two questions, one of them outside the range and one inside the range
    {"id": 5, "clarificationQuestions": [
        {"publishedAt": "2017-03-22T06:00:00.669156Z"},
        {"publishedAt": "2017-03-23T06:00:00.669156Z"}
    ], 'title': 'Confounded Title', 'framework': {'family': 'digital-outcomes-and-specialists'}},

    # a brief with questions over the weekend
    {"id": 6, "clarificationQuestions": [
        {"publishedAt": "2017-03-17T18:00:00.669156Z"},
        {"publishedAt": "2017-03-18T06:00:00.669156Z"},
        {"publishedAt": "2017-03-19T06:00:00.669156Z"},  # Sunday
        {"publishedAt": "2017-03-20T06:00:00.669156Z"},
    ]},
    # a brief with questions on exactly the start date
    {"id": 7, "clarificationQuestions": [
        {"publishedAt": "2017-03-22T08:00:00.000000Z"}
    ]}
]

FILTERED_BRIEFS = [ALL_BRIEFS[3], ALL_BRIEFS[4], ALL_BRIEFS[5]]


MODULE_UNDER_TEST = 'dmscripts.notify_suppliers_of_new_questions_answers'


def test_get_live_briefs_with_new_questions_and_answers_between_two_dates():
    data_api_client = mock.Mock()

    data_api_client.find_briefs_iter.return_value = iter(ALL_BRIEFS)
    briefs = get_live_briefs_with_new_questions_and_answers_between_two_dates(
        data_api_client, datetime(2017, 3, 22, hour=8), datetime(2017, 3, 23, hour=8)
    )
    data_api_client.find_briefs_iter.assert_called_once_with(
        status="live", human=True, with_clarification_questions=True
    )
    assert briefs == FILTERED_BRIEFS


@pytest.mark.parametrize("brief,brief_responses,expected_result", [
    (FILTERED_BRIEFS[0], {"briefResponses": [{"briefId": FILTERED_BRIEFS[0]["id"], "supplierId": 11111}]}, [11111]),
    (
        FILTERED_BRIEFS[1],
        {
            "briefResponses": [
                {"briefId": FILTERED_BRIEFS[1]["id"], "supplierId": 11111},
                {"briefId": FILTERED_BRIEFS[1]["id"], "supplierId": 11112}]
        },
        [11111, 11112]
    ),
    (FILTERED_BRIEFS[2], {"briefResponses": []}, []),
])
def test_get_ids_of_suppliers_who_started_or_finished_applying(brief, brief_responses, expected_result):
    data_api_client = mock.Mock()
    data_api_client.find_brief_responses.return_value = brief_responses

    assert get_ids_of_suppliers_who_started_or_finished_applying(data_api_client, brief) == expected_result
    assert data_api_client.find_brief_responses.call_args_list == [
        mock.call(brief_id=brief['id'], status='draft,submitted')
    ]


@pytest.mark.parametrize("brief,audit_events,expected_result", [
    (
        FILTERED_BRIEFS[0],
        {"auditEvents": [
            {"data": {"briefId": FILTERED_BRIEFS[0]["id"], "question": "can you help me?", "supplierId": 11111}},
            {"data": {"briefId": FILTERED_BRIEFS[0]["id"], "question": "please can you help me?", "supplierId": 11111}},
            {"data": {"briefId": FILTERED_BRIEFS[0]["id"], "question": "can you help me?", "supplierId": 11112}}
        ]},
        [11111, 11111, 11112]
    ), (
        FILTERED_BRIEFS[1],
        {"auditEvents": [{
            "data": {
                "briefId": FILTERED_BRIEFS[1]["id"],
                "question": "can you help me?",
                "supplierId": 11111
            }
        }]},
        [11111]
    ),
    (FILTERED_BRIEFS[2], {"auditEvents": []}, []),
])
def test_get_ids_of_suppliers_who_asked_a_clarification_question(brief, audit_events, expected_result):
    data_api_client = mock.Mock()
    data_api_client.find_audit_events.return_value = audit_events

    assert get_ids_of_suppliers_who_asked_a_clarification_question(data_api_client, brief) == expected_result


@mock.patch(MODULE_UNDER_TEST + '.get_ids_of_suppliers_who_asked_a_clarification_question', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.get_ids_of_suppliers_who_started_or_finished_applying', autospec=True)
def test_get_ids_of_interested_suppliers_for_briefs(
    get_ids_of_suppliers_who_started_applying,
    get_ids_of_suppliers_who_asked_a_clarification_question
):
    briefs = FILTERED_BRIEFS

    get_ids_of_suppliers_who_started_applying.side_effect = (
        [11111, 11112],
        [11111],
        []
    )

    get_ids_of_suppliers_who_asked_a_clarification_question.side_effect = (
        [11111, 11111, 11113],
        [11111],
        [11111, 11112]
    )

    briefs_and_suppliers = get_ids_of_interested_suppliers_for_briefs(mock.Mock(), briefs)

    expected_result = {
        11111: [FILTERED_BRIEFS[0]["id"], FILTERED_BRIEFS[1]["id"], FILTERED_BRIEFS[2]["id"]],
        11112: [FILTERED_BRIEFS[0]["id"], FILTERED_BRIEFS[2]["id"]],
        11113: [FILTERED_BRIEFS[0]["id"]]
    }

    for brief_id, supplier_ids in briefs_and_suppliers.items():
        assert brief_id in expected_result.keys()
        assert sorted(supplier_ids) == expected_result[brief_id]


def test_invert_a_dictionary_so_supplier_id_is_key_and_brief_id_is_value():
    dictionary_to_invert = {
        FILTERED_BRIEFS[0]["id"]: [11111, 11112, 11113],
        FILTERED_BRIEFS[1]["id"]: [11111],
        FILTERED_BRIEFS[2]["id"]: [11111, 11112]
    }

    expected_result = {
        11111: [FILTERED_BRIEFS[0]["id"], FILTERED_BRIEFS[1]["id"], FILTERED_BRIEFS[2]["id"]],
        11112: [FILTERED_BRIEFS[0]["id"], FILTERED_BRIEFS[2]["id"]],
        11113: [FILTERED_BRIEFS[0]["id"]]
    }

    assert invert_a_dictionary_so_supplier_id_is_key_and_brief_id_is_value(dictionary_to_invert) == expected_result


def test_get_supplier_email_addresses_by_supplier_id_filters_out_inactive_users():
    data_api_client = mock.Mock()
    data_api_client.find_users.return_value = {
        'users': [
            {'id': 1, 'emailAddress': 'bananas@example.com', 'active': False},
            {'id': 2, 'emailAddress': 'mangoes@example.com', 'active': True},
            {'id': 3, 'emailAddress': 'guava@example.com', 'active': True}
        ]
    }

    assert get_supplier_email_addresses_by_supplier_id(data_api_client, 1) == [
        'mangoes@example.com', 'guava@example.com'
    ]
    assert data_api_client.find_users.call_args == mock.call(supplier_id=1)


def test_create_context_for_supplier():
    briefs = [FILTERED_BRIEFS[0], FILTERED_BRIEFS[1], FILTERED_BRIEFS[2]]

    with freeze_time('2017-04-19 08:00:00'):
        assert create_context_for_supplier('preview', briefs) == {
            'briefs': [
                {
                    'brief_title': 'Amazing Title',
                    'brief_link': 'https://www.preview.marketplace.team/digital-outcomes-and-specialists/opportunities/3?utm_id=20170419qa'  # noqa
                },
                {
                    'brief_title': 'Brilliant Title',
                    'brief_link': 'https://www.preview.marketplace.team/digital-outcomes-and-specialists/opportunities/4?utm_id=20170419qa'  # noqa
                },
                {
                    'brief_title': 'Confounded Title',
                    'brief_link': 'https://www.preview.marketplace.team/digital-outcomes-and-specialists/opportunities/5?utm_id=20170419qa'  # noqa
                },
            ]
        }


def test_create_context_for_supplier_returns_correct_production_url():
    with freeze_time('2017-04-19 08:00:00'):
        assert create_context_for_supplier('production', [FILTERED_BRIEFS[0]]) == {
            'briefs': [
                {
                    'brief_title': 'Amazing Title',
                    'brief_link': 'https://www.digitalmarketplace.service.gov.uk/'
                                  'digital-outcomes-and-specialists/opportunities/3?utm_id=20170419qa'
                }
            ]
        }


def test_get_template_personalisation_renders_multiple_briefs():
    context = {
        'briefs': [
            {
                'brief_title': 'Amazing Title',
                'brief_link': 'https://www.digitalmarketplace.service.gov.uk/'
                              'digital-outcomes-and-specialists/opportunities/3?utm_id=19990420qa'
            },
            {
                'brief_title': 'Brilliant Title',
                'brief_link': 'https://www.digitalmarketplace.service.gov.uk/'
                              'digital-outcomes-and-specialists/opportunities/4?utm_id=19990420qa'
            }
        ]
    }

    with freeze_time('1999-04-20 08:00:00'):
        template_personalisation = get_template_personalisation(context)

    assert (
        template_personalisation["briefs"]
        ==
        "https://www.digitalmarketplace.service.gov.uk/"
        "digital-outcomes-and-specialists/opportunities/3?utm_id=19990420qa"
        "\n"
        "https://www.digitalmarketplace.service.gov.uk/"
        "digital-outcomes-and-specialists/opportunities/4?utm_id=19990420qa"
    )


@mock.patch(MODULE_UNDER_TEST + '.DMNotifyClient.send_email')
def test_send_emails_calls_notify_api_client(send_email):
    logger = mock.Mock()

    send_supplier_emails(
        NOTIFY_API_KEY,
        ['a@example.com', 'a2@example.com'],
        {'briefs': [
            {
                'brief_title': 'Amazing Title',
                'brief_link': 'https://www.digitalmarketplace.service.gov.uk/'
                              'digital-outcomes-and-specialists/opportunities/3?utm_id=20170419qa'
            },
            {
                'brief_title': 'Brilliant Title',
                'brief_link': 'https://www.digitalmarketplace.service.gov.uk/'
                              'digital-outcomes-and-specialists/opportunities/4?utm_id=20170419qa'
            },
        ]},
        logger
    )

    assert send_email.call_count == 2
    send_email.assert_any_call(
        email_address="a@example.com",
        template_name_or_id=mock.ANY,
        template_personalisation={
            "briefs": "https://www.digitalmarketplace.service.gov.uk/"
                      "digital-outcomes-and-specialists/opportunities/3?utm_id=20170419qa"
                      "\n"
                      "https://www.digitalmarketplace.service.gov.uk/"
                      "digital-outcomes-and-specialists/opportunities/4?utm_id=20170419qa",
        }
    )
    send_email.assert_any_call(
        email_address="a2@example.com",
        template_name_or_id=mock.ANY,
        template_personalisation={
            "briefs": "https://www.digitalmarketplace.service.gov.uk/"
                      "digital-outcomes-and-specialists/opportunities/3?utm_id=20170419qa"
                      "\n"
                      "https://www.digitalmarketplace.service.gov.uk/"
                      "digital-outcomes-and-specialists/opportunities/4?utm_id=20170419qa",
        }
    )


@mock.patch(MODULE_UNDER_TEST + '.send_supplier_emails', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.get_supplier_email_addresses_by_supplier_id', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.get_ids_of_interested_suppliers_for_briefs', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.get_live_briefs_with_new_questions_and_answers_between_two_dates', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.dmapiclient.DataAPIClient')
def test_main_calls_functions(
    data_api_client,
    get_live_briefs_with_new_questions_and_answers_between_two_dates,
    get_ids_of_interested_suppliers_for_briefs,
    get_supplier_email_addresses_by_supplier_id,
    send_supplier_emails
):
    brief0, brief1, brief2 = FILTERED_BRIEFS[0], FILTERED_BRIEFS[1], FILTERED_BRIEFS[2]
    get_live_briefs_with_new_questions_and_answers_between_two_dates.return_value = [
        brief0, brief1, brief2
    ]
    get_ids_of_interested_suppliers_for_briefs.return_value = {
        3: [brief0['id'], brief1['id']],
        4: [brief2['id']]
    }
    get_supplier_email_addresses_by_supplier_id.side_effect = [
        ['a@example.com', 'a2@example.com'], ['b@example.com']
    ]

    with freeze_time('2017-04-19 08:00:00'):
        result = main('api_url', 'api_token', NOTIFY_API_KEY, 'preview', dry_run=False)

    assert result
    assert data_api_client.call_args == mock.call('api_url', 'api_token')
    assert get_live_briefs_with_new_questions_and_answers_between_two_dates.call_args_list == [
        mock.call(data_api_client.return_value, datetime(2017, 4, 18, hour=8), datetime(2017, 4, 19, hour=8))
    ]
    assert get_ids_of_interested_suppliers_for_briefs.call_args == \
        mock.call(
            data_api_client.return_value,
            get_live_briefs_with_new_questions_and_answers_between_two_dates.return_value
        )
    assert get_supplier_email_addresses_by_supplier_id.call_args_list == [
        mock.call(data_api_client.return_value, 3),
        mock.call(data_api_client.return_value, 4),
    ]
    assert send_supplier_emails.call_args_list == [
        mock.call(
            NOTIFY_API_KEY,
            ['a@example.com', 'a2@example.com'],
            {'briefs': [
                {
                    'brief_title': 'Amazing Title',
                    'brief_link': 'https://www.preview.marketplace.team/'
                                  'digital-outcomes-and-specialists/opportunities/3?utm_id=20170419qa'},
                {
                    'brief_title': 'Brilliant Title',
                    'brief_link': 'https://www.preview.marketplace.team/'
                                  'digital-outcomes-and-specialists/opportunities/4?utm_id=20170419qa'}
            ]},
            mock.ANY
        ),
        mock.call(
            NOTIFY_API_KEY,
            ['b@example.com'],
            {'briefs': [
                {
                    'brief_title': 'Confounded Title',
                    'brief_link': 'https://www.preview.marketplace.team/'
                                  'digital-outcomes-and-specialists/opportunities/5?utm_id=20170419qa'}
            ]},
            mock.ANY
        ),
    ]


@mock.patch(MODULE_UNDER_TEST + '.send_supplier_emails', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.get_supplier_email_addresses_by_supplier_id', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.get_ids_of_interested_suppliers_for_briefs', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.get_live_briefs_with_new_questions_and_answers_between_two_dates', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.dmapiclient.DataAPIClient')
def test_main_can_restrict_to_custom_list_of_suppliers(
    data_api_client,
    get_live_briefs_with_new_questions_and_answers_between_two_dates,
    get_ids_of_interested_suppliers_for_briefs,
    get_supplier_email_addresses_by_supplier_id,
    send_supplier_emails
):
    get_live_briefs_with_new_questions_and_answers_between_two_dates.return_value = [
        FILTERED_BRIEFS[0]
    ]
    get_ids_of_interested_suppliers_for_briefs.return_value = {
        3: [FILTERED_BRIEFS[0]["id"]],
        4: [FILTERED_BRIEFS[0]["id"]],
    }
    get_supplier_email_addresses_by_supplier_id.return_value = ['a@example.com']

    with freeze_time('2017-04-19 08:00:00'):
        main('api_url', 'api_token', NOTIFY_API_KEY, 'preview', dry_run=False, supplier_ids=[4])

    assert data_api_client.call_args == mock.call('api_url', 'api_token')
    assert get_supplier_email_addresses_by_supplier_id.call_args_list == [
        mock.call(data_api_client.return_value, 4),
    ]
    assert send_supplier_emails.call_args_list == [
        mock.call(
            NOTIFY_API_KEY,
            ['a@example.com'],
            {'briefs': [
                {
                    'brief_title': 'Amazing Title',
                    'brief_link': 'https://www.preview.marketplace.team/'
                                  'digital-outcomes-and-specialists/opportunities/3?utm_id=20170419qa'}
            ]},
            mock.ANY
        ),
    ]


@mock.patch(MODULE_UNDER_TEST + '.logger', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.send_supplier_emails', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.get_supplier_email_addresses_by_supplier_id', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.get_ids_of_interested_suppliers_for_briefs', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.get_live_briefs_with_new_questions_and_answers_between_two_dates', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.dmapiclient.DataAPIClient')
def test_main_catches_and_logs_email_errors_returns_false(
    data_api_client,
    get_live_briefs_with_new_questions_and_answers_between_two_dates,
    get_ids_of_interested_suppliers_for_briefs,
    get_supplier_email_addresses_by_supplier_id,
    send_supplier_emails,
    logger
):
    get_live_briefs_with_new_questions_and_answers_between_two_dates.return_value = [
        FILTERED_BRIEFS[0]
    ]
    get_ids_of_interested_suppliers_for_briefs.return_value = {
        3: [FILTERED_BRIEFS[0]["id"]],
        4: [FILTERED_BRIEFS[0]["id"]],
        5: [FILTERED_BRIEFS[0]["id"]],
    }
    get_supplier_email_addresses_by_supplier_id.side_effect = [
        ['a@example.com'], ['b@example.com'], ['c@example.com']
    ]
    send_supplier_emails.side_effect = [
        EmailError,
        True,
        EmailError
    ]

    result = main('api_url', 'api_token', 'M', 'preview', dry_run=False)

    assert result is False
    assert send_supplier_emails.call_args_list == [
        mock.call('M', ['a@example.com'], mock.ANY, mock.ANY),
        mock.call('M', ['b@example.com'], mock.ANY, mock.ANY),
        mock.call('M', ['c@example.com'], mock.ANY, mock.ANY),
    ]
    assert logger.error.call_args == mock.call(
        'Email sending failed for the following supplier IDs: {supplier_ids}',
        extra={"supplier_ids": "3,5"}
    )


@mock.patch(MODULE_UNDER_TEST + '.logger', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.send_supplier_emails', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.get_supplier_email_addresses_by_supplier_id', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.get_ids_of_interested_suppliers_for_briefs', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.get_live_briefs_with_new_questions_and_answers_between_two_dates', autospec=True)
@mock.patch(MODULE_UNDER_TEST + '.dmapiclient.DataAPIClient')
def test_main_does_not_try_to_send_email_if_no_active_users_for_supplier(
    data_api_client,
    get_live_briefs_with_new_questions_and_answers_between_two_dates,
    get_ids_of_interested_suppliers_for_briefs,
    get_supplier_email_addresses_by_supplier_id,
    send_supplier_emails,
    logger
):
    get_live_briefs_with_new_questions_and_answers_between_two_dates.return_value = [
        FILTERED_BRIEFS[0]
    ]
    get_ids_of_interested_suppliers_for_briefs.return_value = {
        3: [FILTERED_BRIEFS[0]["id"]]
    }
    get_supplier_email_addresses_by_supplier_id.return_value = []

    result = main('api_url', 'api_token', 'M', 'preview', dry_run=False)

    assert result is True
    assert not send_supplier_emails.called
    assert logger.info.call_args == mock.call(
        'Email not sent for the following supplier ID due to no active users: {supplier_id}',
        extra={"supplier_id": 3, "brief_ids_list": "3"}
    )
