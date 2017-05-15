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
def test_main(get_supplier_users, find_user_emails):
    supplier_users = {
        100: [{'supplier_id': 100, 'email address': 'email1@email.com'}]
    }
    framework_services = iter([
        {'supplierId': 100}
    ])
    lot_data = {
        "lot_slug": "digital-specialists",
        "list_id": "my list id",
        "framework_slug": "digital-outcomes-and-specialists-2"
    }
    list_of_emails = ['email1@email.com', 'email2@email.com']

    data_api_client = mock.MagicMock(spec=DataAPIClient)
    data_api_client.find_services_iter.return_value = framework_services
    get_supplier_users.return_value = supplier_users
    find_user_emails.return_value = list_of_emails
    dm_mailchimp_client = mock.MagicMock(spec=DMMailChimpClient)
    logger = mock.MagicMock()

    assert main(data_api_client, dm_mailchimp_client, lot_data, logger) is True
    data_api_client.find_services_iter.assert_called_once_with(
        framework="digital-outcomes-and-specialists-2", lot="digital-specialists"
    )
    get_supplier_users.assert_called_once()
    find_user_emails.assert_called_once_with(supplier_users, framework_services)

    dm_mailchimp_client.subscribe_new_emails_to_list.assert_called_once_with("my list id", list_of_emails)
