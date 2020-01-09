from dmapiclient import DataAPIClient
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.email_helpers import scripts_notify_client
from dmscripts.helpers.logging_helpers import configure_logger, logging
from dmutils.email.exceptions import EmailError
from dmutils.email.helpers import hash_string
from dmutils.env_helpers import get_api_endpoint_from_stage
from dmutils.formats import utctoshorttimelongdateformat


NOTIFY_TEMPLATE_ID = '25c7c763-fe51-418f-8e51-130c391edc35'

MESSAGES = {
    'unconfirmed_company_details': '* confirm your company details\n',
    'incomplete_declaration': '* finish your supplier declaration\n',
    'no_services': '* mark at least one of your services as complete\n',
    'unsubmitted_services': '* check that all services to be submitted have been marked as complete '
                            '({} currently incomplete)\n'
}


def send_notification(mail_client, message, framework, email, supplier_id, dry_run):
    prefix = "[Dry Run] " if dry_run else ""
    mail_client.logger.info(
        f"{prefix}Sending email to supplier '{supplier_id}' "
        f"user '{hash_string(email)}'"
    )
    if not dry_run:
        try:
            mail_client.send_email(
                email,
                NOTIFY_TEMPLATE_ID,
                {
                    'message': message,
                    'framework_name': framework['name'],
                    'framework_slug': framework['slug'],
                    'application_deadline': utctoshorttimelongdateformat(framework['applicationsCloseAtUTC'])
                },
                allow_resend=False
            )
        except EmailError as e:
            mail_client.logger.error(
                f"Error sending email to supplier '{supplier_id}' "
                f"user '{hash_string(email)}': {e}"
            )
            return 1
    return 0


def notify_suppliers_with_incomplete_applications(framework_slug, stage, notify_api_key, dry_run):
    logger = configure_logger({"dmapiclient": logging.INFO})
    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage), auth_token=get_auth_token('api', stage)
    )

    framework = data_api_client.get_framework(framework_slug)['frameworks']
    if framework['status'] != 'open':
        raise ValueError("Suppliers cannot amend applications unless the framework is open.")

    mail_client = scripts_notify_client(notify_api_key, logger=logger)
    error_count = 0

    for sf in data_api_client.find_framework_suppliers_iter(framework_slug):
        message = ''
        if not sf.get('applicationCompanyDetailsConfirmed', None):
            message += MESSAGES['unconfirmed_company_details']
        if not sf.get('declaration', {'status': None}).get('status', None) == 'complete':
            message += MESSAGES['incomplete_declaration']

        submitted_draft_services, unsubmitted_draft_services = 0, 0
        for service in data_api_client.find_draft_services_iter(sf['supplierId'], framework=framework_slug):
            if service.get('status') == 'not-submitted':
                unsubmitted_draft_services += 1
            if service.get('status') == 'submitted':
                submitted_draft_services += 1
        if submitted_draft_services == 0:
            message += MESSAGES['no_services']
        elif unsubmitted_draft_services > 0:
            message += MESSAGES['unsubmitted_services'].format(unsubmitted_draft_services)

        if message:
            primary_email = sf.get('declaration', {'primaryContactEmail': None}).get('primaryContactEmail', None)
            if primary_email:
                error_count += send_notification(
                    mail_client,
                    message,
                    framework,
                    primary_email,
                    sf['supplierId'],
                    dry_run
                )
            for user in data_api_client.find_users(supplier_id=sf['supplierId']).get('users', []):
                if user['active']:
                    error_count += send_notification(
                        mail_client,
                        message,
                        framework,
                        user['emailAddress'],
                        sf['supplierId'],
                        dry_run
                    )

    return error_count
