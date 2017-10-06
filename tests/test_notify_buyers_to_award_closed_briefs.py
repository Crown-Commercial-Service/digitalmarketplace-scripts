import mock
from freezegun import freeze_time
import datetime
import pytest

from dmutils.email import EmailError
from dmscripts import notify_buyers_to_award_closed_briefs


class TestSendEmailToBriefUserViaNotify:

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
            failed_user = notify_buyers_to_award_closed_briefs.send_email_to_brief_user_via_notify(
                notify_client, 'NOTIFY_TEMPLATE_ID', self.brief['users'][0], self.brief, None, None
            )

        assert failed_user is None
        assert notify_client.send_email.call_args_list == [
            mock.call(
                'a@example.com',
                'NOTIFY_TEMPLATE_ID',
                {
                    'brief_id': 100,
                    'brief_title': 'My brief title',
                    'framework_slug': 'framework-slug',
                    'lot_slug': 'lot-slug',
                    'utm_date': '20170101',
                },
                allow_resend=False
            )
        ]

    def test_send_email_to_brief_user_via_notify_skips_inactive_users(self):
        notify_client = mock.Mock()

        with freeze_time('2017-01-01'):
            failed_user = notify_buyers_to_award_closed_briefs.send_email_to_brief_user_via_notify(
                notify_client, 'NOTIFY_TEMPLATE_ID', self.brief['users'][1], self.brief, None, None
            )

        assert failed_user is None
        notify_client.assert_not_called()

    def test_send_email_to_brief_user_via_notify_sends_to_user_present_in_user_id_list(self):
        notify_client = mock.Mock()

        with freeze_time('2017-01-01'):
            failed_user = notify_buyers_to_award_closed_briefs.send_email_to_brief_user_via_notify(
                notify_client, 'NOTIFY_TEMPLATE_ID', self.brief['users'][0], self.brief, [9], None
            )

        assert failed_user is None
        notify_client.assert_not_called()

    def test_send_email_to_brief_user_via_notify_skips_user_if_not_present_in_user_id_list(self):
        notify_client = mock.Mock()

        with freeze_time('2017-01-01'):
            failed_user = notify_buyers_to_award_closed_briefs.send_email_to_brief_user_via_notify(
                notify_client, 'NOTIFY_TEMPLATE_ID', self.brief['users'][0], self.brief, [123], None
            )

        assert failed_user is None
        notify_client.assert_not_called()

    def test_send_email_to_brief_user_via_notify_catches_email_errors_and_returns_user_id(self):
        notify_client = mock.Mock()
        notify_client.send_email.side_effect = [EmailError]

        with freeze_time('2017-01-01'):
            failed_user = notify_buyers_to_award_closed_briefs.send_email_to_brief_user_via_notify(
                notify_client, 'NOTIFY_TEMPLATE_ID', self.brief['users'][2], self.brief, None, None
            )

        assert failed_user == 999

    @mock.patch('dmscripts.notify_buyers_to_award_closed_briefs.logger', autospec=True)
    def test_send_email_to_brief_user_via_notify_logs_instead_of_sending_for_dry_runs(self, logger):
        notify_client = mock.Mock()
        notify_client.send_email.return_value = self._get_notify_email_api_response()

        with freeze_time('2017-01-01'):
            failed_user = notify_buyers_to_award_closed_briefs.send_email_to_brief_user_via_notify(
                notify_client, 'NOTIFY_TEMPLATE_ID', self.brief['users'][0], self.brief, None, True
            )

        assert failed_user is None
        assert logger.info.call_args_list == [mock.call(
            "Would notify {no_of_users} user(s) about brief ID: {brief_id} - '{brief_title}'",
            extra={'brief_title': 'My brief title', 'brief_id': 100, 'no_of_users': 3}
        )]
        notify_client.assert_not_called()


@mock.patch('dmscripts.notify_buyers_to_award_closed_briefs.DMNotifyClient', autospec=True)
@mock.patch('dmscripts.notify_buyers_to_award_closed_briefs.send_email_to_brief_user_via_notify')
@mock.patch('dmscripts.helpers.brief_data_helpers.get_briefs_closed_on_date')
@mock.patch('dmscripts.notify_buyers_to_award_closed_briefs.logger', autospec=True)
class TestMain:

    OFFSET_DAYS = 28

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

    def test_main_sends_email_to_brief_user_via_notify_for_each_user_on_each_closed_brief(
            self, logger, get_briefs_closed_on_date, send_email_to_brief_user_via_notify, notify_client):
        get_briefs_closed_on_date.return_value = [self.brief1, self.brief2]
        send_email_to_brief_user_via_notify.return_value = []

        with freeze_time('2016-01-29 03:04:05'):
            assert notify_buyers_to_award_closed_briefs.main(
                'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', self.OFFSET_DAYS,
                date_closed='2016-01-01', dry_run=None
            )
            get_briefs_closed_on_date.assert_called_once_with(mock.ANY, datetime.date(2016, 1, 1))
            notify_client.assert_called_once_with('NOTIFY_KEY', logger=mock.ANY)
            assert send_email_to_brief_user_via_notify.call_args_list == [
                mock.call(
                    notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief1['users'][0], self.brief1, None, None
                ),
                mock.call(
                    notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief2['users'][0], self.brief2, None, None
                ),
            ]
            assert logger.info.call_args_list == [
                mock.call("Data API URL: {data_api_url}", extra={'data_api_url': 'URL'}),
                mock.call(
                    "{briefs_count} closed brief(s) found with closing date {date_closed}",
                    extra={'briefs_count': 2, 'date_closed': datetime.date(2016, 1, 1)}
                )
            ]

    def test_main_notifies_about_briefs_closed_on_date_8_weeks_ago_using_offset_days(
        self, logger, get_briefs_closed_on_date, send_email_to_brief_user_via_notify, notify_client
    ):
        get_briefs_closed_on_date.return_value = [self.brief1, self.brief2]
        send_email_to_brief_user_via_notify.return_value = []

        with freeze_time('2016-02-26 03:04:05'):
            assert notify_buyers_to_award_closed_briefs.main(
                'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', offset_days=56, date_closed=None, dry_run=None
            )
            get_briefs_closed_on_date.assert_called_once_with(mock.ANY, datetime.date(2016, 1, 1))
            notify_client.assert_called_once_with('NOTIFY_KEY', logger=mock.ANY)
            assert send_email_to_brief_user_via_notify.call_args_list == [
                mock.call(
                    notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief1['users'][0], self.brief1, None, None
                ),
                mock.call(
                    notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief2['users'][0], self.brief2, None, None
                ),
            ]

    def test_main_fails_when_send_email_to_brief_user_via_notify_fails(
            self, logger, get_briefs_closed_on_date, send_email_to_brief_user_via_notify, notify_client):
        get_briefs_closed_on_date.return_value = [self.brief1, self.brief2, self.brief3]
        send_email_to_brief_user_via_notify.side_effect = [9, None, 999, 9999]

        assert not notify_buyers_to_award_closed_briefs.main(
            'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', self.OFFSET_DAYS,
            date_closed="2017-01-01", dry_run=None
        )
        notify_client.assert_called_with('NOTIFY_KEY', logger=mock.ANY)
        assert send_email_to_brief_user_via_notify.call_args_list == [
            mock.call(
                notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief1['users'][0], self.brief1, None, None
            ),
            mock.call(
                notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief2['users'][0], self.brief2, None, None
            ),
            mock.call(
                notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief3['users'][0], self.brief3, None, None
            ),
            mock.call(
                notify_client.return_value, 'NOTIFY_TEMPLATE_ID', self.brief3['users'][1], self.brief3, None, None
            ),
        ]
        assert logger.error.call_args_list == [
            mock.call(
                'Email sending failed for the following buyer users of brief ID {brief_id}: {buyer_ids}',
                extra={'brief_id': 100, 'buyer_ids': '9'}
            ),
            mock.call(
                'Email sending failed for the following buyer users of brief ID {brief_id}: {buyer_ids}',
                extra={'brief_id': 300, 'buyer_ids': '999,9999'}
            ),
            mock.call(
                'All failures for award closed briefs notification on closing date {date_closed}: {all_failed_users}',
                extra={'date_closed': '2017-01-01', 'all_failed_users': '9,999,9999'}
            )
        ]

    def test_main_with_no_briefs_logs_and_returns_true(
            self, logger, get_briefs_closed_on_date, send_email_to_brief_user_via_notify, notify_client):
        get_briefs_closed_on_date.return_value = []

        assert notify_buyers_to_award_closed_briefs.main(
            'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', self.OFFSET_DAYS,
            date_closed='2017-01-01', dry_run=None
        )
        assert logger.info.call_args_list == [
            mock.call("Data API URL: {data_api_url}", extra={'data_api_url': 'URL'}),
            mock.call("No briefs closed on {date_closed}", extra={"date_closed": datetime.date(2017, 1, 1)})
        ]
        notify_client.assert_called_with('NOTIFY_KEY', logger=mock.ANY)
        send_email_to_brief_user_via_notify.assert_not_called()

    @pytest.mark.parametrize('offset_days, date_closed', [(28, '2016-01-02'), (56, '2015-12-05')])
    def test_main_doesnt_allow_date_closed_to_be_less_than_x_days_ago_by_default(
            self, logger, get_briefs_closed_on_date, send_email_to_brief_user_via_notify, notify_client,
            offset_days, date_closed
    ):
        get_briefs_closed_on_date.return_value = [self.brief1, self.brief2]

        with freeze_time('2016-01-29 08:34:05'):
            assert not notify_buyers_to_award_closed_briefs.main(
                'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', offset_days,
                date_closed=date_closed, dry_run=None,
            )
        notify_client.assert_not_called()
        send_email_to_brief_user_via_notify.assert_not_called()
        logger.error.assert_called_with(
            'Not allowed to notify about briefs that closed less than {} days ago', offset_days
        )
