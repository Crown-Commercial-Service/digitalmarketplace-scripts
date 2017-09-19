import mock
from freezegun import freeze_time
import datetime
import pytest

from dmutils.email.exceptions import EmailError
from dmscripts import notify_buyers_to_award_closed_briefs


class TestNotifyUsers:

    brief = {
        'id': 100,
        'title': 'My brief title',
        'lotSlug': 'lot-slug',
        'frameworkSlug': 'framework-slug',
        'users': [
            {'emailAddress': 'a@example.com', 'id': 9, 'active': True},
            {'emailAddress': 'b@example.com', 'id': 99, 'active': False},
            {'emailAddress': 'c@example.com', 'id': 999, 'active': True},
        ],
    }

    @staticmethod
    def _get_notify_email_api_response(status="success"):
        return {
            "id": "notify_id",
            "reference": "client reference",
            "email_address": "something@example.com",
            "type": "email",
            "status": status,
            "template": {
                "version": 1,  # template version num # required
                "id": 123,  # template id # required
                "uri": "/v2/template/123/1",  # required
            },
            "body": "I love notifications",
            "subject": "Your recently closed brief",
            "created_at": "2017-01-01",
            "sent_at": "2017-01-01",
            "completed_at": "2017-01-01"
        }

    def test_notify_users_sends_emails_to_all_active_users(self):
        notify_client = mock.Mock()
        notify_client.send_email.return_value = self._get_notify_email_api_response()

        with freeze_time('2017-01-01'):
            failed_users = notify_buyers_to_award_closed_briefs.notify_users(
                notify_client, 'NOTIFY_TEMPLATE_ID', self.brief, None
            )

        assert failed_users == []
        assert notify_client.send_email.call_args_list == [
            mock.call(
                'a@example.com',
                'NOTIFY_TEMPLATE_ID',
                {'brief_id': 100, 'brief_title': 'My brief title', 'utm_date': '20170101'},
                allow_resend=False
            ),
            mock.call(
                'c@example.com',
                'NOTIFY_TEMPLATE_ID',
                {'brief_id': 100, 'brief_title': 'My brief title', 'utm_date': '20170101'},
                allow_resend=False
            ),
        ]

    def test_notify_user_filters_by_user_id_list(self):
        notify_client = mock.Mock()
        notify_client.send_email.return_value = self._get_notify_email_api_response()

        with freeze_time('2017-01-01'):
            failed_users = notify_buyers_to_award_closed_briefs.notify_users(
                notify_client, 'NOTIFY_TEMPLATE_ID', self.brief, [999]
            )

        assert failed_users == []
        assert notify_client.send_email.call_args_list == [
            mock.call(
                'c@example.com',
                'NOTIFY_TEMPLATE_ID',
                {'brief_id': 100, 'brief_title': 'My brief title', 'utm_date': '20170101'},
                allow_resend=False
            ),
        ]

    def test_notify_users_catches_email_errors(self):
        notify_client = mock.Mock()
        notify_client.send_email.side_effect = [
            True,
            EmailError  # fail on second email
        ]

        with freeze_time('2017-01-01'):
            failed_users = notify_buyers_to_award_closed_briefs.notify_users(
                notify_client, 'NOTIFY_TEMPLATE_ID', self.brief, None
            )

        assert failed_users == [999]
        assert notify_client.send_email.call_args_list == [
            mock.call(
                'a@example.com', 'NOTIFY_TEMPLATE_ID',
                {'brief_id': 100, 'brief_title': 'My brief title', 'utm_date': '20170101'}, allow_resend=False
            ),
            mock.call(
                'c@example.com', 'NOTIFY_TEMPLATE_ID',
                {'brief_id': 100, 'brief_title': 'My brief title', 'utm_date': '20170101'}, allow_resend=False
            ),
        ]


@mock.patch('dmscripts.notify_buyers_to_award_closed_briefs.DMNotifyClient')
@mock.patch('dmscripts.notify_buyers_to_award_closed_briefs.notify_users')
@mock.patch('dmscripts.helpers.brief_data_helpers.get_closed_briefs')
@mock.patch('dmscripts.notify_buyers_to_award_closed_briefs.logger')
class TestMain:

    brief1 = {
        'id': 100,
        'title': 'Extra 3 hrs sleep (for govt)',
        'users': [
            {'emailAddress': 'failed@example.com', 'id': 9}
        ]
    }
    brief2 = {
        'id': 200,
        'title': 'Mochi making machine (for govt)',
        'users': [
            {'emailAddress': 'success@example.com', 'id': 99}
        ]
    }
    brief3 = {
        'id': 300,
        'title': 'Yet another requirement',
        'users': [
            {'emailAddress': 'success300@example.com', 'id': 999},
            {'emailAddress': 'failed300@example.com', 'id': 9999}
        ]
    }

    def test_main_calls_notify_for_each_closed_brief(self, logger, get_closed_briefs, notify_users, notify_client):
        get_closed_briefs.return_value = [self.brief1, self.brief2]
        notify_users.return_value = []

        with freeze_time('2016-01-29 03:04:05'):
            assert notify_buyers_to_award_closed_briefs.main(
                'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', date_closed='2016-01-01', dry_run=None
            )
            get_closed_briefs.assert_called_once_with(mock.ANY, datetime.date(2016, 1, 1))
            notify_client.assert_called_once_with('NOTIFY_KEY', logger=mock.ANY)
            notify_users.assert_has_calls([
                mock.call(notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief1, None),
                mock.call(notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief2, None),
            ])
            assert logger.info.call_args_list == [
                mock.call("Data API URL: {data_api_url}", extra={'data_api_url': 'URL'}),
                mock.call(
                    "Notifying users about {briefs_count} closed brief(s)",
                    extra={'briefs_count': 2}
                ),
                mock.call(
                    "Notifying {no_of_users} user(s) about brief ID: {brief_id} - '{brief_title}'",
                    extra={
                        'brief_title': 'Extra 3 hrs sleep (for govt)',
                        'brief_id': 100,
                        'no_of_users': 1,
                    }
                ),
                mock.call(
                    "Notifying {no_of_users} user(s) about brief ID: {brief_id} - '{brief_title}'",
                    extra={
                        'brief_title': 'Mochi making machine (for govt)',
                        'brief_id': 200,
                        'no_of_users': 1,
                    }
                )
            ]

    def test_main_calls_notify_for_each_closed_brief_with_user_in_user_id_list(
            self, logger, get_closed_briefs, notify_users, notify_client):
        get_closed_briefs.return_value = [self.brief1, self.brief2]
        notify_users.return_value = []

        with freeze_time('2016-01-29 03:04:05'):
            assert notify_buyers_to_award_closed_briefs.main(
                'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', date_closed='2016-01-01', dry_run=None,
                user_id_list=[99]
            )
            get_closed_briefs.assert_called_once_with(mock.ANY, datetime.date(2016, 1, 1))
            notify_client.assert_called_once_with('NOTIFY_KEY', logger=mock.ANY)
            notify_users.assert_has_calls([
                mock.call(notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief2, [99]),
            ])
            assert logger.info.call_args_list == [
                mock.call("Data API URL: {data_api_url}", extra={'data_api_url': 'URL'}),
                mock.call(
                    "Notifying users about {briefs_count} closed brief(s)",
                    extra={'briefs_count': 1}
                ),
                mock.call(
                    "Notifying {no_of_users} user(s) about brief ID: {brief_id} - '{brief_title}'",
                    extra={
                        'brief_title': 'Mochi making machine (for govt)',
                        'brief_id': 200,
                        'no_of_users': 1,
                    }
                )
            ]

    def test_main_notifies_about_briefs_closed_on_date_8_weeks_ago_using_offset_days(
            self, logger, get_closed_briefs, notify_users, notify_client):
        get_closed_briefs.return_value = [self.brief1, self.brief2]
        notify_users.return_value = []

        with freeze_time('2016-02-26 03:04:05'):
            assert notify_buyers_to_award_closed_briefs.main(
                'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', date_closed=None, dry_run=None, offset_days=56
            )
            get_closed_briefs.assert_called_once_with(mock.ANY, datetime.date(2016, 1, 1))
            notify_client.assert_called_once_with('NOTIFY_KEY', logger=mock.ANY)
            notify_users.assert_has_calls([
                mock.call(notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief1, None),
                mock.call(notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief2, None),
            ])

    def test_main_fails_when_notify_users_fails(self, logger, get_closed_briefs, notify_users, notify_client):

        get_closed_briefs.return_value = [self.brief1, self.brief2, self.brief3]
        notify_users.side_effect = [
            [9],
            [],
            [999]
        ]

        assert not notify_buyers_to_award_closed_briefs.main(
            'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', date_closed="2017-01-01", dry_run=None
        )
        notify_client.assert_called_with('NOTIFY_KEY', logger=mock.ANY)
        notify_users.assert_has_calls([
            mock.call(notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief1, None),
            mock.call(notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief2, None),
            mock.call(notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief3, None),
        ])
        assert logger.error.call_args_list == [
            mock.call(
                'Email sending failed for the following buyer users of brief ID {brief_id}: {buyer_ids}',
                extra={'brief_id': 100, 'buyer_ids': '9'}
            ),
            mock.call(
                'Email sending failed for the following buyer users of brief ID {brief_id}: {buyer_ids}',
                extra={'brief_id': 300, 'buyer_ids': '999'}
            ),
            mock.call(
                'All failures for award closed briefs notification on closing date {date_closed}: {all_failed_users}',
                extra={'date_closed': '2017-01-01', 'all_failed_users': '9,999'}
            )
        ]

    def test_main_with_no_briefs_logs_and_returns_true(self, logger, get_closed_briefs, notify_users, notify_client):
        get_closed_briefs.return_value = []

        assert notify_buyers_to_award_closed_briefs.main(
            'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', date_closed='2017-01-01', dry_run=None
        )
        logger.info.assert_has_calls([
            mock.call("Data API URL: {data_api_url}", extra={'data_api_url': 'URL'}),
            mock.call("No briefs closed on {date_closed}", extra={"date_closed": datetime.date(2017, 1, 1)})
        ])
        notify_client.assert_called_with('NOTIFY_KEY', logger=mock.ANY)
        notify_users.assert_not_called()

    @pytest.mark.parametrize('offset_days, date_closed', [(28, '2016-01-02'), (56, '2015-12-05')])
    def test_main_doesnt_allow_date_closed_to_be_less_than_x_days_ago_by_default(
            self, logger, get_closed_briefs, notify_users, notify_client, offset_days, date_closed):
        get_closed_briefs.return_value = [self.brief1, self.brief2]

        with freeze_time('2016-01-29 08:34:05'):
            assert not notify_buyers_to_award_closed_briefs.main(
                'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', date_closed=date_closed, dry_run=None,
                offset_days=offset_days
            )
        notify_client.assert_not_called()
        notify_users.assert_not_called()
        logger.error.assert_called_with(
            'Not allowed to notify about briefs that closed less than {} days ago', offset_days
        )

    def test_main_dry_run_does_not_call_notify_users(self, logger, get_closed_briefs, notify_users, notify_client):
        get_closed_briefs.return_value = [self.brief1, self.brief2, self.brief3]

        assert notify_buyers_to_award_closed_briefs.main(
            'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', date_closed=None, dry_run=True
        )
        assert logger.info.call_args_list == [
            mock.call("Data API URL: {data_api_url}", extra={'data_api_url': 'URL'}),
            mock.call("Notifying users about {briefs_count} closed brief(s)", extra={'briefs_count': 3}),
            mock.call(
                "Would notify {no_of_users} user(s) about brief ID: {brief_id} - '{brief_title}'",
                extra={'no_of_users': 1,  'brief_id': 100, 'brief_title': 'Extra 3 hrs sleep (for govt)'}
            ),
            mock.call(
                "Would notify {no_of_users} user(s) about brief ID: {brief_id} - '{brief_title}'",
                extra={'no_of_users': 1, 'brief_id': 200, 'brief_title': 'Mochi making machine (for govt)'}
            ),
            mock.call(
                "Would notify {no_of_users} user(s) about brief ID: {brief_id} - '{brief_title}'",
                extra={'no_of_users': 2, 'brief_id': 300, 'brief_title': 'Yet another requirement'}
            ),
        ]
        notify_client.assert_not_called()
        notify_users.assert_not_called()
