import mock
from freezegun import freeze_time
import datetime

from dmutils.email.exceptions import EmailError
from dmscripts import notify_buyers_to_award_closed_briefs


class TestNotifyUsers:

    brief = {
        'id': 100,
        'title': 'My brief title',
        'lotSlug': 'lot-slug',
        'frameworkSlug': 'framework-slug',
        'users': [
            {'emailAddress': 'a@example.com', 'active': True},
            {'emailAddress': 'b@example.com', 'active': False},
            {'emailAddress': 'c@example.com', 'active': True},
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

        failed_users = notify_buyers_to_award_closed_briefs.notify_users(
            notify_client, 'NOTIFY_TEMPLATE_ID', self.brief
        )

        assert failed_users == []
        assert notify_client.send_email.call_args_list == [
            mock.call(
                'a@example.com',
                'NOTIFY_TEMPLATE_ID',
                {'brief_id': 100, 'brief_title': 'My brief title'},
                allow_resend=False
            ),
            mock.call(
                'c@example.com',
                'NOTIFY_TEMPLATE_ID',
                {'brief_id': 100, 'brief_title': 'My brief title'},
                allow_resend=False
            ),
        ]

    def test_notify_users_catches_email_errors(self):
        notify_client = mock.Mock()
        notify_client.send_email.side_effect = [
            True,
            EmailError  # fail on second email
        ]

        failed_users = notify_buyers_to_award_closed_briefs.notify_users(
            notify_client, 'NOTIFY_TEMPLATE_ID', self.brief
        )
        assert failed_users == ['c@example.com']
        # TODO: assert that the first email sent ok


@mock.patch('dmscripts.notify_buyers_to_award_closed_briefs.DMNotifyClient')
@mock.patch('dmscripts.notify_buyers_to_award_closed_briefs.notify_users')
@mock.patch('dmscripts.helpers.brief_data_helpers.get_closed_briefs')
@mock.patch('dmscripts.notify_buyers_to_award_closed_briefs.logger')
class TestMain:

    def test_main_calls_notify_for_each_closed_brief(self, logger, get_closed_briefs, notify_users, notify_client):
        brief1 = {'id': 100, 'title': 'Extra 3 hrs sleep (for govt)', 'users': ['failed@example.com']}
        brief2 = {'id': 200, 'title': 'Mochi making machine (for govt)', 'users': ['success@example.com']}

        get_closed_briefs.return_value = [brief1, brief2]

        notify_users.return_value = []

        with freeze_time('2016-01-29 03:04:05'):
            assert notify_buyers_to_award_closed_briefs.main(
                'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', '2016-01-01', False
            )
            get_closed_briefs.assert_called_once_with(mock.ANY, datetime.date(2016, 1, 1))
            notify_client.assert_called_once_with('NOTIFY_KEY', logger=mock.ANY)
            notify_users.assert_has_calls([
                mock.call(notify_client.return_value, 'NOTIFY_TEMPLATE_ID', brief1),
                mock.call(notify_client.return_value, 'NOTIFY_TEMPLATE_ID', brief2),
            ])
            assert logger.info.call_args_list == [
                mock.call("Data API URL: {data_api_url}", extra={'data_api_url': 'URL'}),
                mock.call(
                    "Notifying users about {briefs_count} closed briefs",
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

    def test_main_fails_when_notify_users_fails(self, logger, get_closed_briefs, notify_users, notify_client):
        brief1 = {'id': 100, 'title': 'Extra 3 hrs sleep (for govt)', 'users': ['failed@example.com']}
        brief2 = {'id': 200, 'title': 'Mochi making machine (for govt)', 'users': ['success@example.com']}
        get_closed_briefs.return_value = [brief1, brief2]

        notify_users.side_effect = [
            ['failed@example.com'],
            []
        ]

        assert not notify_buyers_to_award_closed_briefs.main(
            'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', None, False
        )
        notify_client.assert_called_with('NOTIFY_KEY', logger=mock.ANY)
        notify_users.assert_has_calls([
            mock.call(notify_client.return_value, 'NOTIFY_TEMPLATE_ID', brief1),
            mock.call(notify_client.return_value, 'NOTIFY_TEMPLATE_ID', brief2),
        ])
        # TODO: assert logging

    def test_main_with_no_briefs_logs_and_returns_true(self, logger, get_closed_briefs, notify_users, notify_client):
        get_closed_briefs.return_value = []

        assert notify_buyers_to_award_closed_briefs.main(
            'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', '2017-01-01', False
        )
        logger.info.assert_has_calls([
            mock.call("Data API URL: {data_api_url}", extra={'data_api_url': 'URL'}),
            mock.call("No briefs closed on {date_closed}", extra={"date_closed": datetime.date(2017, 1, 1)})
        ])
        notify_client.assert_called_with('NOTIFY_KEY', logger=mock.ANY)
        notify_users.assert_not_called()

    def test_main_doesnt_allow_date_closed_to_be_less_than_4_weeks_ago(
            self, logger, get_closed_briefs, notify_users, notify_client):
        get_closed_briefs.return_value = [
            {'id': 100},
            {'id': 200},
        ]

        with freeze_time('2016-01-29 08:34:05'):
            assert not notify_buyers_to_award_closed_briefs.main(
                'URL', 'API_KEY', 'NOTIFY_KEY', 'NOTIFY_TEMPLATE_ID', '2016-01-02', False
            )
        notify_client.assert_not_called()
        notify_users.assert_not_called()

    def test_main_dry_run_does_not_call_notify_users(self, logger, get_closed_briefs, notify_users, notify_client):
        get_closed_briefs.return_value = [
            {'id': 100, 'title': 'Extra 3 hrs sleep (for govt)', 'users': ['a@example.com', 'b@example.com']},
            {'id': 200, 'title': 'Mochi making machine (for govt)', 'users': ['c@example.com']},
        ]

        assert notify_buyers_to_award_closed_briefs.main(
            'URL',
            'API_KEY',
            'NOTIFY_KEY',
            'NOTIFY_TEMPLATE_ID',
            None,
            True
        )
        logger.info.assert_has_calls([
            mock.call("Data API URL: {data_api_url}", extra={'data_api_url': 'URL'}),
            mock.call("Notifying users about {briefs_count} closed briefs", extra={'briefs_count': 2}),
            mock.call(
                "Would notify {no_of_users} user(s) about brief ID: {brief_id} - '{brief_title}'",
                extra={'no_of_users': 2,  'brief_id': 100, 'brief_title': 'Extra 3 hrs sleep (for govt)'}
            ),
            mock.call(
                "Would notify {no_of_users} user(s) about brief ID: {brief_id} - '{brief_title}'",
                extra={'no_of_users': 1, 'brief_id': 200, 'brief_title': 'Mochi making machine (for govt)'}
            ),
        ])
        notify_client.assert_not_called()
        notify_users.assert_not_called()
