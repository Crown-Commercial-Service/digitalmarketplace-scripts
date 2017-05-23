import mock

from dmapiclient import DataAPIClient
from dmscripts.upload_dos_opportunities_email_list import find_user_emails, main, SupplierFrameworkData
from dmutils.email.dm_mailchimp import DMMailChimpClient


def test_find_user_emails():
    supplier_users = {
        100: [{'supplier_id': 100, 'email address': 'email1@email.com'}],
        102: [
            {'supplier_id': 102, 'email address': 'email2@email.com'},
            {'supplier_id': 102, 'email address': 'email3@email.com'}
        ],
        103: [{'supplier_id': 103, 'email address': 'email4@email.com'}],
    }

    services = [
        {'supplierId': 102},
        {'supplierId': 103}
    ]
    assert find_user_emails(supplier_users, services) == ['email2@email.com', 'email3@email.com', 'email4@email.com']


@mock.patch("dmscripts.upload_dos_opportunities_email_list.find_user_emails", autospec=True)
@mock.patch.object(SupplierFrameworkData, 'get_supplier_users', spec=SupplierFrameworkData.get_supplier_users)
class TestMain(object):
    LOT_DATA = {
        "lot_slug": "digital-specialists",
        "list_id": "my list id",
        "framework_slug": "digital-outcomes-and-specialists-2"
    }

    LIST_OF_EMAILS = ['email1@email.com', 'email2@email.com']

    def setup_method(self, method):
        self.data_api_client = mock.MagicMock(spec=DataAPIClient)
        self.dm_mailchimp_client = mock.MagicMock(spec=DMMailChimpClient)
        self.logger = mock.MagicMock()

    def test_main(self, get_supplier_users, find_user_emails):
        supplier_users = {
            100: [
                {'supplier_id': 100, 'email address': 'email1@email.com'},
                {'supplier_id': 100, 'email address': 'email2@email.com'}
            ]
        }
        framework_services = iter([
            {'supplierId': 100}
        ])

        self.data_api_client.find_services_iter.return_value = framework_services
        get_supplier_users.return_value = supplier_users
        find_user_emails.return_value = self.LIST_OF_EMAILS
        self.dm_mailchimp_client.get_email_addresses_from_list.return_value = ['EMAIL1@email.com']

        assert main(self.data_api_client, self.dm_mailchimp_client, self.LOT_DATA, self.logger) is True
        self.data_api_client.find_services_iter.assert_called_once_with(
            framework="digital-outcomes-and-specialists-2", lot="digital-specialists"
        )
        get_supplier_users.assert_called_once()
        find_user_emails.assert_called_once_with(supplier_users, framework_services)
        self.dm_mailchimp_client.get_email_addresses_from_list.assert_called_once_with("my list id")
        self.dm_mailchimp_client.subscribe_new_emails_to_list.assert_called_once_with(
            "my list id", ['email2@email.com']
        )

    def test_main_returns_false_if_subscribing_emails_fails(self, get_supplier_users, find_user_emails):
        find_user_emails.return_value = self.LIST_OF_EMAILS
        self.dm_mailchimp_client.subscribe_new_emails_to_list.return_value = False

        assert main(self.data_api_client, self.dm_mailchimp_client, self.LOT_DATA, self.logger) is False
        self.dm_mailchimp_client.subscribe_new_emails_to_list.assert_called_once_with("my list id", self.LIST_OF_EMAILS)
