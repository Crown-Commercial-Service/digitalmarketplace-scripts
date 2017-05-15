from dmscripts.helpers.supplier_data_helpers import SupplierFrameworkData


def find_user_emails(supplier_users, services):
    """Return email addresses for any supplier who has a service in services."""
    email_addresses = []
    for service in services:
        for user in supplier_users.get(service['supplierId'], []):
            email_addresses.append(user['email address'])
    return email_addresses


def main(data_api_client, mailchimp_client, lot_data):
    data_helper = SupplierFrameworkData(data_api_client, lot_data["framework_slug"])
    supplier_users = data_helper.get_supplier_users()

    framework_services = data_api_client.find_services_iter(
        framework=lot_data["framework_slug"], lot=lot_data["lot_slug"]
    )
    emails = find_user_emails(supplier_users, framework_services)
    print emails
    mailchimp_client.subscribe_new_emails_to_list(lot_data["list_id"], emails)
    return True
