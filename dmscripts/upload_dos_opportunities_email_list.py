from dmscripts.helpers.supplier_data_helpers import SupplierFrameworkData


def find_user_emails(supplier_users, services):
    """Return email addresses for any supplier who has a service in services."""
    email_addresses = []
    for service in services:
        for user in supplier_users.get(service['supplierId'], []):
            email_addresses.append(user['email address'])
    return email_addresses


def lowercase_list(x):
    return [item.lower() for item in x]


def main(data_api_client, mailchimp_client, lot_data, logger):
    logger.info(
        "Begin mailchimp email list updating process for {} lot".format(lot_data["lot_slug"]),
        extra={"lot_data": lot_data}
    )

    data_helper = SupplierFrameworkData(data_api_client, lot_data["framework_slug"])
    supplier_users = data_helper.get_supplier_users()
    framework_services = data_api_client.find_services_iter(
        framework=lot_data["framework_slug"], lot=lot_data["lot_slug"]
    )

    emails = find_user_emails(supplier_users, framework_services)
    logger.info(
        "{} emails have been found for lot {}".format(len(emails), lot_data["lot_slug"])
    )

    existing_mailchimp_emails = mailchimp_client.get_email_addresses_from_list(lot_data["list_id"])
    logger.info(
        "{} existing emails found on list {}".format(len(existing_mailchimp_emails), lot_data["list_id"])
    )

    # lowercase required because mailchimp may capatalise emails addresses returned from the mailchimp API based on it's
    # on how it stores both the lowercase hash but also the original (potentially capatilised) email address
    new_emails = list(set(lowercase_list(emails)) - set(lowercase_list(existing_mailchimp_emails)))
    logger.info(
        "Subscribing {} new emails to mailchimp list {}".format(len(new_emails), lot_data["list_id"])
    )
    if not mailchimp_client.subscribe_new_emails_to_list(lot_data["list_id"], new_emails):
        return False

    return True
