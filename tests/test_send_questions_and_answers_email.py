import mock
import pytest
from freezegun import freeze_time

from datetime import datetime

from dmscripts.send_questions_and_answers_email import (
    main,
    get_live_briefs_with_new_questions_and_answers_between_two_dates,
    get_ids_of_suppliers_who_started_applying,
    get_ids_of_suppliers_who_asked_a_clarification_question
)


def test_get_live_briefs_with_new_questions_and_answers_between_two_dates():
    data_api_client = mock.Mock()
    brief_iter_values = [
        # a brief with no questions
        {"clarificationQuestions": []},

        # a brief with a question outside of the date range
        {"clarificationQuestions": [{"publishedAt": "2017-03-22T06:00:00.669156Z"}]},

        # a brief with two questions outside of the date range
        {"clarificationQuestions": [
            {"publishedAt": "2017-03-21T06:00:00.669156Z"},
            {"publishedAt": "2017-03-22T06:00:00.669156Z"}
        ]},

        # a brief with a question inside of the date range
        {"clarificationQuestions": [{"publishedAt": "2017-03-23T06:00:00.669156Z"}]},

        # a brief with two questions inside of the date range
        {"clarificationQuestions": [
            {"publishedAt": "2017-03-22T18:00:00.669156Z"},
            {"publishedAt": "2017-03-23T06:00:00.669156Z"}
        ]},

        # a brief with two questions, one of them outside the range and one inside the range
        {"clarificationQuestions": [
            {"publishedAt": "2017-03-22T06:00:00.669156Z"},
            {"publishedAt": "2017-03-23T06:00:00.669156Z"}
        ]},

        # a brief with questions over the weekend
        {"clarificationQuestions": [
            {"publishedAt": "2017-03-17T18:00:00.669156Z"},
            {"publishedAt": "2017-03-18T06:00:00.669156Z"},
            {"publishedAt": "2017-03-19T06:00:00.669156Z"},  # Sunday
            {"publishedAt": "2017-03-20T06:00:00.669156Z"},
        ]}
    ]

    data_api_client.find_briefs_iter.return_value = iter(brief_iter_values)
    briefs = get_live_briefs_with_new_questions_and_answers_between_two_dates(
        data_api_client, datetime(2017, 3, 22, hour=8), datetime(2017, 3, 23, hour=8)
    )
    data_api_client.find_briefs_iter.assert_called_once_with(status="live", human=True)
    assert briefs == [
        {"clarificationQuestions": [{"publishedAt": "2017-03-23T06:00:00.669156Z"}]},
        {"clarificationQuestions": [
            {"publishedAt": "2017-03-22T18:00:00.669156Z"},
            {"publishedAt": "2017-03-23T06:00:00.669156Z"}
        ]},
        {"clarificationQuestions": [
            {"publishedAt": "2017-03-22T06:00:00.669156Z"},
            {"publishedAt": "2017-03-23T06:00:00.669156Z"}
        ]},
    ]


def test_get_ids_of_suppliers_who_started_applying():
    data_api_client = mock.Mock()
    briefs = [
        {
            "id": 1,
            "clarificationQuestions": [{"publishedAt": "2017-03-23T06:00:00.669156Z"}]
        },
        {
            "id": 2,
            "clarificationQuestions": [
                {"publishedAt": "2017-03-22T18:00:00.669156Z"},
                {"publishedAt": "2017-03-23T06:00:00.669156Z"}
            ]
        },
        {
            "id": 3,
            "clarificationQuestions": [
                {"publishedAt": "2017-03-22T06:00:00.669156Z"},
                {"publishedAt": "2017-03-23T06:00:00.669156Z"}
            ]
        },
    ]

    data_api_client.find_brief_responses.side_effect = (
        {"briefResponses": [{"briefId": 1, "supplierId": 11111}]},
        {"briefResponses": [{"briefId": 2, "supplierId": 11111}, {"briefId": 2, "supplierId": 11112}]},
        {"briefResponses": []}
    )

    assert get_ids_of_suppliers_who_started_applying(data_api_client, briefs) == {1: [11111], 2: [11111, 11112], 3: []}


def test_get_ids_of_suppliers_who_asked_a_clarification_question():
    data_api_client = mock.Mock()
    briefs = [
        {
            "id": 1,
            "clarificationQuestions": [{"publishedAt": "2017-03-23T06:00:00.669156Z"}]
        },
        {
            "id": 2,
            "clarificationQuestions": [
                {"publishedAt": "2017-03-22T18:00:00.669156Z"},
                {"publishedAt": "2017-03-23T06:00:00.669156Z"}
            ]
        },
        {
            "id": 3,
            "clarificationQuestions": [
                {"publishedAt": "2017-03-22T06:00:00.669156Z"},
                {"publishedAt": "2017-03-23T06:00:00.669156Z"}
            ]
        },
    ]

    # we're going to have a list of audit events for clarification questions for each brief

    data_api_client.find_audit_events.side_effect = (
        # three questions (but only two unique suppliers)
        {"auditEvents": [
            {"data": {"briefId": 1, "question": "can you help me?", "supplierId": 11111}},
            {"data": {"briefId": 1, "question": "please can you help me?", "supplierId": 11111}},
            {"data": {"briefId": 1, "question": "can you help me?", "supplierId": 11112}}
        ]},
        # one question
        {"auditEvents": [{"data": {"briefId": 2, "question": "can you help me?", "supplierId": 11111}}]},
        # no questions
        {"auditEvents": []}
    )

    assert get_ids_of_suppliers_who_asked_a_clarification_question(data_api_client, briefs) == {1: [11111, 11111, 11112], 2: [11111], 3: []}

@pytest.mark.parametrize("number_of_days,start_date,end_date", [
    (1, datetime(2017, 4, 18, hour=8), datetime(2017, 4, 19, hour=8)),
    (3, datetime(2017, 4, 16, hour=8), datetime(2017, 4, 19, hour=8))
])
@mock.patch(
    'dmscripts.send_questions_and_answers_email.get_live_briefs_with_new_questions_and_answers_between_two_dates',
    autospec=True
)
def test_main_gets_live_briefs_correct_number_of_days(
    get_live_briefs_with_new_questions_and_answers_between_two_dates,
    number_of_days,
    start_date,
    end_date
):
    with freeze_time('2017-04-19 08:00:00'):
        main(mock.MagicMock(), number_of_days)
        get_live_briefs_with_new_questions_and_answers_between_two_dates.assert_called_once_with(
            mock.ANY, start_date, end_date
        )
