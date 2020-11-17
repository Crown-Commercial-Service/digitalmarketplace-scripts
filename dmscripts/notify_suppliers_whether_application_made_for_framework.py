from dmutils.email.exceptions import EmailError, EmailTemplateError
from dmutils.email.helpers import hash_string
from dmscripts.helpers.supplier_data_helpers import AppliedToFrameworkSupplierContextForNotify


NOTIFY_TEMPLATES = {
    'application_made': 'de02a7e3-80f6-4391-818c-48326e1f4688',
    'application_not_made': '87a126b4-7909-4b63-b981-d3c3d6a558ff'
}


def notify_suppliers_whether_application_made(
    api_client, mail_client, framework_slug, logger, dry_run=False, supplier_ids=None
):

    context_helper = AppliedToFrameworkSupplierContextForNotify(api_client, framework_slug, supplier_ids=supplier_ids)
    context_helper.populate_data()
    prefix = "[Dry Run] " if dry_run else ""
    error_count = 0
    for supplier_id, users in context_helper.get_suppliers_with_users_personalisations():
        logger.info(f"{prefix}Supplier '{supplier_id}'")

        for user, personalisation in users:
            user_email = user["email address"]
            template_key = 'application_made' if personalisation['applied'] else 'application_not_made'
            template = NOTIFY_TEMPLATES[template_key]

            logger.info(
                f"{prefix}Sending '{template_key}' email to supplier '{supplier_id}' user '{hash_string(user_email)}'")

            if dry_run:
                continue

            try:
                mail_client.send_email(user_email, template, personalisation, allow_resend=False)
            except EmailError as e:
                logger.error(f"Error sending email to supplier '{supplier_id}' user '{hash_string(user_email)}': {e}")

                if isinstance(e, EmailTemplateError):
                    raise  # do not try to continue

                error_count += 1

    return error_count
