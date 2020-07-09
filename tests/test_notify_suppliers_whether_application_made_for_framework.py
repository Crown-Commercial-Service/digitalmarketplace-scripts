from logging import Logger
import mock
from dmutils.email import DMNotifyClient
from dmutils.email.exceptions import EmailError
from dmapiclient import DataAPIClient
from dmscripts.notify_suppliers_whether_application_made_for_framework import (
    notify_suppliers_whether_application_made,
    NOTIFY_TEMPLATES,
)


class TestNotifySuppliersWhetherApplicationMade:

    def setup(self):
        self.data_api_client = mock.create_autospec(DataAPIClient, instance=True)
        self.data_api_client.get_framework.return_value = {
            "frameworks": {
                "slug": "g-cloud-12",
                "name": "G-Cloud 12",
                "frameworkExpiresAtUTC": "2017-12-31T23:59:59.999999Z",
                "clarificationsCloseAtUTC": "2017-12-31T23:59:59.999999Z",
                "clarificationsPublishAtUTC": "2017-12-31T23:59:59.999999Z",
                'applicationsCloseAtUTC': "2017-12-31T23:59:59.999999Z",
                'intentionToAwardAtUTC': "2017-12-31T23:59:59.999999Z",
                'frameworkLiveAtUTC': "2017-12-31T23:59:59.999999Z"
            }
        }
        self.data_api_client.find_framework_suppliers_iter.return_value = [
            {"supplierId": 712345},
            {"supplierId": 712346},
        ]
        self.data_api_client.export_users.return_value = {
            # This endpoint returns some unusually formatted keys :(
            # See https://github.com/alphagov/digitalmarketplace-api/blob/6ad35e526fcf4d76320159a1a4ac97133a1ce13d/app/main/views/users.py#L417  # noqa
            'users': [
                {'supplier_id': 712345, 'email address': 'user1@example.com', 'application_status': 'no_application'},
                {'supplier_id': 712346, 'email address': 'user2@example.com', 'application_status': 'application'},
                {'supplier_id': 712346, 'email address': 'user3@example.com', 'application_status': 'application'},
            ]
        }
        self.data_api_client.find_draft_services_iter.return_value = {
            # Assume all suppliers have submitted a service
            'services': [
                {'status': 'submitted'}
            ]
        }

        self.notify_client = mock.create_autospec(DMNotifyClient, instance=True)
        self.logger = mock.create_autospec(Logger, instance=True)

    def test_notify_suppliers_whether_application_made_happy_path(self):
        assert notify_suppliers_whether_application_made(
            self.data_api_client,
            self.notify_client,
            'g-cloud-12',
            self.logger,
        ) == 0

        assert self.notify_client.send_email.call_args_list == [
            mock.call(
                "user1@example.com",
                NOTIFY_TEMPLATES['application_not_made'],
                {
                    'intention_to_award_at': 'Sunday 31 December 2017',
                    'framework_name': 'G-Cloud 12',
                    'framework_slug': 'g-cloud-12',
                    'applied': False
                },
                allow_resend=False
            ),
            mock.call(
                "user2@example.com",
                NOTIFY_TEMPLATES['application_made'],
                {
                    'intention_to_award_at': 'Sunday 31 December 2017',
                    'framework_name': 'G-Cloud 12',
                    'framework_slug': 'g-cloud-12',
                    'applied': True
                },
                allow_resend=False
            ),
            mock.call(
                "user3@example.com",
                NOTIFY_TEMPLATES['application_made'],
                {
                    'intention_to_award_at': 'Sunday 31 December 2017',
                    'framework_name': 'G-Cloud 12',
                    'framework_slug': 'g-cloud-12',
                    'applied': True
                },
                allow_resend=False
            ),
        ]
        assert self.logger.info.call_args_list == [
            mock.call("Supplier '712345'"),
            mock.call(
                "Sending 'application_not_made' email to supplier '712345' "
                "user 's2qDcB8cMZHhlyLW-QJ0vBtVAf5p6_MzE-RA_ksP4hA='"
            ),
            mock.call("Supplier '712346'"),
            mock.call(
                "Sending 'application_made' email to supplier '712346' "
                "user 'KzsrnOhCq4tqbGFMsflgS7ig1QLRr0nFJrcrEIlOlbU='"
            ),
            mock.call(
                "Sending 'application_made' email to supplier '712346' "
                "user 'iYYo4oiQ-Te98Ak5He9Ch5xAGkvPG1_STnONn12oy7s='"
            )
        ]

    def test_notify_suppliers_whether_application_made_dry_run(self):
        assert notify_suppliers_whether_application_made(
            self.data_api_client,
            self.notify_client,
            'g-cloud-12',
            self.logger,
            dry_run=True
        ) == 0

        assert self.notify_client.send_email.call_args_list == []
        assert self.logger.info.call_args_list == [
            mock.call("[Dry Run] Supplier '712345'"),
            mock.call(
                "[Dry Run] Sending 'application_not_made' email to supplier '712345' "
                "user 's2qDcB8cMZHhlyLW-QJ0vBtVAf5p6_MzE-RA_ksP4hA='"
            ),
            mock.call("[Dry Run] Supplier '712346'"),
            mock.call(
                "[Dry Run] Sending 'application_made' email to supplier '712346' "
                "user 'KzsrnOhCq4tqbGFMsflgS7ig1QLRr0nFJrcrEIlOlbU='"
            ),
            mock.call(
                "[Dry Run] Sending 'application_made' email to supplier '712346' "
                "user 'iYYo4oiQ-Te98Ak5He9Ch5xAGkvPG1_STnONn12oy7s='"
            )
        ]

    def test_notify_suppliers_whether_application_made_supplier_ids_list(self):
        assert notify_suppliers_whether_application_made(
            self.data_api_client,
            self.notify_client,
            'g-cloud-12',
            self.logger,
            supplier_ids=[712345]
        ) == 0

        assert self.notify_client.send_email.call_args_list == [
            mock.call(
                "user1@example.com",
                NOTIFY_TEMPLATES['application_not_made'],
                {
                    'intention_to_award_at': 'Sunday 31 December 2017',
                    'framework_name': 'G-Cloud 12',
                    'framework_slug': 'g-cloud-12',
                    'applied': False
                },
                allow_resend=False
            )
        ]
        assert self.logger.info.call_args_list == [
            mock.call("Supplier '712345'"),
            mock.call(
                "Sending 'application_not_made' email to supplier '712345' "
                "user 's2qDcB8cMZHhlyLW-QJ0vBtVAf5p6_MzE-RA_ksP4hA='"
            )
        ]

    def test_notify_suppliers_whether_application_made_email_error_logs_supplier_id(self):
        self.notify_client.send_email.side_effect = [
            EmailError("Arghhh!"),  # The first user email fails
            None,
            None
        ]

        assert notify_suppliers_whether_application_made(
            self.data_api_client,
            self.notify_client,
            'g-cloud-12',
            self.logger
        ) == 1

        assert self.logger.info.call_args_list == [
            mock.call("Supplier '712345'"),
            mock.call(
                "Sending 'application_not_made' email to supplier '712345' "
                "user 's2qDcB8cMZHhlyLW-QJ0vBtVAf5p6_MzE-RA_ksP4hA='"
            ),
            mock.call("Supplier '712346'"),
            mock.call(
                "Sending 'application_made' email to supplier '712346' "
                "user 'KzsrnOhCq4tqbGFMsflgS7ig1QLRr0nFJrcrEIlOlbU='"
            ),
            mock.call(
                "Sending 'application_made' email to supplier '712346' "
                "user 'iYYo4oiQ-Te98Ak5He9Ch5xAGkvPG1_STnONn12oy7s='"
            )
        ]
        assert self.logger.error.call_args_list == [
            mock.call(
                "Error sending email to supplier '712345' user 's2qDcB8cMZHhlyLW-QJ0vBtVAf5p6_MzE-RA_ksP4hA=': Arghhh!"
            )
        ]
