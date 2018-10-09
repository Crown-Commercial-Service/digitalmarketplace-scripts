import mock
from freezegun import freeze_time

import datetime

from dmscripts.notify_buyers_when_requirements_close import (
    get_date_closed,
    notify_users,
    main
)
from dmutils.email.exceptions import EmailError


NOTIFY_API_KEY = "1" * 73


class FakeMail(object):
    """An object that equals strings containing all of the given substrings

    Can be used in mock.call comparisons (eg to verify email templates).

    """
    def __init__(self, *substrings):
        self.substrings = substrings

    def __eq__(self, other):
        return all(substring in other for substring in self.substrings)

    def __repr__(self):
        return "<FakeMail: {}>".format(self.substrings)


def test_get_date_closed():
    def check_date_closed(value, expected):
        with freeze_time('2015-01-02 03:04:05'):
            assert get_date_closed(value) == expected

    for value, expected in [
        (None, datetime.date(2015, 1, 1)),
        ('2016-01-02', datetime.date(2016, 1, 2))
    ]:
        check_date_closed(value, expected)


@mock.patch('dmscripts.notify_buyers_when_requirements_close.DMNotifyClient.send_email', autospec=True)
def test_notify_users(send_email):
    notify_users(NOTIFY_API_KEY, 'preview', {
        'id': 100,
        'title': 'My brief title',
        'lotSlug': 'lot-slug',
        'frameworkSlug': 'framework-slug',
        'users': [
            {'emailAddress': 'a@example.com', 'active': True},
            {'emailAddress': 'b@example.com', 'active': False},
            {'emailAddress': 'c@example.com', 'active': True},
        ],
    })

    brief_responses_url = \
        "https://www.preview.marketplace.team" \
        "/buyers/frameworks/framework-slug/requirements/lot-slug/100/responses"

    assert send_email.call_count == 2
    send_email.assert_any_call(
        mock.ANY,  # self
        'a@example.com',
        template_name_or_id=mock.ANY,
        personalisation={
            "brief_title": "My brief title",
            "brief_responses_url": brief_responses_url,
        },
        allow_resend=False,
    )
    send_email.assert_any_call(
        mock.ANY,  # self
        'c@example.com',
        template_name_or_id=mock.ANY,
        personalisation={
            "brief_title": "My brief title",
            "brief_responses_url": brief_responses_url,
        },
        allow_resend=False,
    )


@mock.patch('dmscripts.notify_buyers_when_requirements_close.DMNotifyClient.send_email', autospec=True)
def test_notify_users_returns_false_on_error(send_email):
    send_email.side_effect = EmailError('Error')
    assert not notify_users(NOTIFY_API_KEY, 'preview', {
        'id': 100,
        'title': 'My brief title',
        'lotSlug': 'lot-slug',
        'frameworkSlug': 'framework-slug',
        'users': [
            {'emailAddress': 'a@example.com', 'active': True},
            {'emailAddress': 'b@example.com', 'active': False},
            {'emailAddress': 'c@example.com', 'active': True},
        ],
    })


@mock.patch('dmscripts.notify_buyers_when_requirements_close.notify_users')
@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_briefs_closed_on_date')
def test_main(get_briefs_closed_on_date, notify_users):
    get_briefs_closed_on_date.return_value = [
        {'id': 100},
        {'id': 200},
        {'id': 300},
    ]

    notify_users.return_value = True

    with freeze_time('2016-01-02 03:04:05'):
        assert main('URL', 'API_KEY', NOTIFY_API_KEY, 'preview', '2016-01-02', False)
    get_briefs_closed_on_date.assert_called_once_with(mock.ANY, datetime.date(2016, 1, 2))
    notify_users.assert_has_calls([
        mock.call(NOTIFY_API_KEY, 'preview', {'id': 100}),
        mock.call(NOTIFY_API_KEY, 'preview', {'id': 200}),
        mock.call(NOTIFY_API_KEY, 'preview', {'id': 300}),
    ])


@mock.patch('dmscripts.notify_buyers_when_requirements_close.notify_users')
@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_briefs_closed_on_date')
def test_main_fails_when_notify_users_fails(get_briefs_closed_on_date, notify_users):
    get_briefs_closed_on_date.return_value = [
        {'id': 100},
        {'id': 200},
    ]

    notify_users.return_value = False

    assert not main('URL', 'API_KEY', NOTIFY_API_KEY, 'preview', None, False)


@mock.patch('dmscripts.notify_buyers_when_requirements_close.notify_users')
@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_briefs_closed_on_date')
def test_main_with_no_briefs(get_briefs_closed_on_date, notify_users):
    get_briefs_closed_on_date.return_value = []

    assert main('URL', 'API_KEY', NOTIFY_API_KEY, 'preview', None, False)
    notify_users.assert_not_called()


@mock.patch('dmscripts.notify_buyers_when_requirements_close.notify_users')
@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_briefs_closed_on_date')
def test_main_doesnt_allow_old_date_closed(get_briefs_closed_on_date, notify_users):
    get_briefs_closed_on_date.return_value = [
        {'id': 100},
        {'id': 200},
    ]

    with freeze_time('2016-01-12 03:04:05'):
        assert not main('URL', 'API_KEY', NOTIFY_API_KEY, 'preview', '2016-01-02', False)

    notify_users.assert_not_called()


@mock.patch('dmscripts.notify_buyers_when_requirements_close.notify_users')
@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_briefs_closed_on_date')
def test_main_dry_run(get_briefs_closed_on_date, notify_users):
    get_briefs_closed_on_date.return_value = [
        {'id': 100},
        {'id': 200},
    ]

    assert main('URL', 'API_KEY', NOTIFY_API_KEY, 'preview', None, True)
    notify_users.assert_not_called()
