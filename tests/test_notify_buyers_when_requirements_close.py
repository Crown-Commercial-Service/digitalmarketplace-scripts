import mock
from freezegun import freeze_time

import datetime

from dmscripts.notify_buyers_when_requirements_close import (
    get_date_closed,
    get_notified_briefs,
    notify_users,
    main
)
from dmutils.email.exceptions import EmailError


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
        yield check_date_closed, value, expected


@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_sent_emails')
def test_get_notified_briefs(get_sent_emails):
    get_sent_emails.return_value = [
        {},
        {'metadata': {'brief_id': 100}},
        {'metadata': {'brief_id': 200}},
        {'metadata': {'brief_id': 300}},
        {'metadata': None},
    ]

    assert get_notified_briefs('KEY', datetime.date(2015, 1, 2)) == set([100, 200, 300])
    get_sent_emails.assert_called_once_with('KEY', ['requirements-closed'], date_from='2015-01-02')


@mock.patch('dmscripts.notify_buyers_when_requirements_close.send_email')
def test_notify_users(send_email):
    notify_users('KEY', {
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

    send_email.assert_called_once_with(
        ['a@example.com', 'c@example.com'],
        FakeMail(
            'My brief title',
            '/buyers/frameworks/framework-slug/requirements/lot-slug/100/responses'
        ),
        'KEY',
        u'Next steps for your \u2018My brief title\u2019 requirements',
        'enquiries@digitalmarketplace.service.gov.uk',
        'Digital Marketplace Admin',
        ['requirements-closed'],
        logger=mock.ANY,
        metadata={'brief_id': 100}
    )


@mock.patch('dmscripts.notify_buyers_when_requirements_close.send_email')
def test_notify_users_returns_false_on_error(send_email):
    send_email.side_effect = EmailError('Error')
    assert not notify_users('KEY', {
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
@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_notified_briefs')
@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_briefs_closed_on_date')
def test_main(get_briefs_closed_on_date, get_notified_briefs, notify_users):
    get_notified_briefs.return_value = set([200])
    get_briefs_closed_on_date.return_value = [
        {'id': 100},
        {'id': 200},
        {'id': 300},
    ]

    notify_users.return_value = True

    with freeze_time('2016-01-02 03:04:05'):
        assert main('URL', 'API_KEY', 'KEY', '2016-01-02', False)
    get_briefs_closed_on_date.assert_called_once_with(mock.ANY, datetime.date(2016, 1, 2))
    get_notified_briefs.assert_called_once_with('KEY', datetime.date(2016, 1, 2))
    notify_users.assert_has_calls([
        mock.call('KEY', {'id': 100}),
        mock.call('KEY', {'id': 300}),
    ])


@mock.patch('dmscripts.notify_buyers_when_requirements_close.notify_users')
@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_notified_briefs')
@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_briefs_closed_on_date')
def test_main_fails_when_notify_users_fails(get_briefs_closed_on_date, get_notified_briefs, notify_users):
    get_briefs_closed_on_date.return_value = [
        {'id': 100},
        {'id': 200},
    ]

    notify_users.return_value = False

    assert not main('URL', 'API_KEY', 'KEY', None, False)


@mock.patch('dmscripts.notify_buyers_when_requirements_close.notify_users')
@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_notified_briefs')
@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_briefs_closed_on_date')
def test_main_with_no_briefs(get_briefs_closed_on_date, get_notified_briefs, notify_users):
    get_briefs_closed_on_date.return_value = []

    assert main('URL', 'API_KEY', 'KEY', None, False)
    get_notified_briefs.assert_not_called()
    notify_users.assert_not_called()


@mock.patch('dmscripts.notify_buyers_when_requirements_close.notify_users')
@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_notified_briefs')
@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_briefs_closed_on_date')
def test_main_doesnt_allow_old_date_closed(get_briefs_closed_on_date, get_notified_briefs, notify_users):
    get_briefs_closed_on_date.return_value = [
        {'id': 100},
        {'id': 200},
    ]

    with freeze_time('2016-01-12 03:04:05'):
        assert not main('URL', 'API_KEY', 'KEY', '2016-01-02', False)

    get_notified_briefs.assert_not_called()
    notify_users.assert_not_called()


@mock.patch('dmscripts.notify_buyers_when_requirements_close.notify_users')
@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_notified_briefs')
@mock.patch('dmscripts.notify_buyers_when_requirements_close.get_briefs_closed_on_date')
def test_main_dry_run(get_briefs_closed_on_date, get_notified_briefs, notify_users):
    get_briefs_closed_on_date.return_value = [
        {'id': 100},
        {'id': 200},
    ]

    assert main('URL', 'API_KEY', 'KEY', None, True)
    notify_users.assert_not_called()
