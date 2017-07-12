import dmapiclient

from datetime import datetime, date, timedelta

from dmscripts.helpers import env_helpers, logging_helpers
from dmscripts.helpers.html_helpers import render_html
from dmscripts.helpers.logging_helpers import logging
from dmutils.email.dm_mandrill import send_email
from dmutils.formats import DATETIME_FORMAT


EMAIL_SUBJECT = "New question and answer responses on the Digital Marketplace"
EMAIL_FROM_ADDRESS = "do-not-reply@digitalmarketplace.service.gov.uk"
EMAIL_FROM_NAME = "Digital Marketplace Team"


logger = logging_helpers.configure_logger({'dmapiclient': logging.INFO})


def get_live_briefs_with_new_questions_and_answers_between_two_dates(data_api_client, start_date, end_date):
    briefs = data_api_client.find_briefs_iter(status='live', human=True, with_clarification_questions=True)

    # return a list of briefs that contain clarification questions published between the start data and the end date
    return [brief for brief in briefs if brief.get('clarificationQuestions') and any(
        datetime.strptime(question['publishedAt'], DATETIME_FORMAT) >= start_date
        and datetime.strptime(question['publishedAt'], DATETIME_FORMAT) <= end_date
        for question in brief['clarificationQuestions']
    )]


def get_ids_of_suppliers_who_started_applying(data_api_client, brief):
    responses = data_api_client.find_brief_responses(brief_id=brief["id"])
    return [response["supplierId"] for response in responses["briefResponses"]]


def get_ids_of_suppliers_who_asked_a_clarification_question(data_api_client, brief):
    audit_events = data_api_client.find_audit_events(
        audit_type=dmapiclient.audit.AuditTypes.send_clarification_question,
        object_type='briefs',
        object_id=brief['id']
    )
    return [audit_event['data']['supplierId'] for audit_event in audit_events['auditEvents']]


def get_ids_of_interested_suppliers_for_briefs(data_api_client, briefs):
    interested_suppliers = {}
    for brief in briefs:
        suppliers_who_applied = get_ids_of_suppliers_who_started_applying(data_api_client, brief)
        suppliers_who_asked_a_question = get_ids_of_suppliers_who_asked_a_clarification_question(data_api_client, brief)
        interested_suppliers[brief['id']] = list(set(suppliers_who_applied + suppliers_who_asked_a_question))

    return invert_a_dictionary_so_supplier_id_is_key_and_brief_id_is_value(interested_suppliers)


def invert_a_dictionary_so_supplier_id_is_key_and_brief_id_is_value(dictionary_to_invert):
    inverted_dic = {}
    for brief_id, list_of_supplier_ids in dictionary_to_invert.items():
        for supplier_id in list_of_supplier_ids:
            inverted_dic.setdefault(supplier_id, []).append(brief_id)

    return inverted_dic


def get_supplier_email_addresses_by_supplier_id(data_api_client, supplier_id):
    response = data_api_client.find_users(supplier_id=supplier_id)
    return [user['emailAddress'] for user in response['users']]


def _get_link_domain(stage):
    return env_helpers.get_api_endpoint_from_stage(stage, app='www')


def create_context_for_supplier(stage, supplier_briefs):
    return {
        'briefs': [
            {
                'brief_title': brief['title'],
                'brief_link': '{0}/{1}/opportunities/{2}'.format(
                    _get_link_domain(stage),
                    brief['frameworkFramework'], brief['id']
                )
            } for brief in supplier_briefs
        ]
    }


def get_html_content(context):

    return render_html("email_templates/suppliers_new_briefs_questions_answers.html", data={
        "briefs": context['briefs'], "today": datetime.utcnow()
    })


def send_supplier_emails(email_api_key, email_addresses, supplier_context, logger):

    send_email(
        email_addresses,
        get_html_content(supplier_context),
        email_api_key,
        EMAIL_SUBJECT,
        EMAIL_FROM_ADDRESS,
        EMAIL_FROM_NAME,
        ["supplier-new-brief-questions-answers"],
        logger=logger
    )


def main(data_api_url, data_api_token, email_api_key, stage, dry_run, exclude_supplier_ids=[]):
    logger.info("Begin to send brief update notification emails")

    # get today at 8 in the morning
    end_date = datetime.utcnow().replace(hour=8, minute=0, second=0, microsecond=0)
    # get yesterday at 8 in the morning
    start_date = end_date - timedelta(days=1)

    # Initialise data API client
    data_api_client = dmapiclient.DataAPIClient(data_api_url, data_api_token)

    # we want to find all questions and answers that were submitted between start and end dates
    briefs = get_live_briefs_with_new_questions_and_answers_between_two_dates(data_api_client, start_date, end_date)
    logger.info(
        "{} briefs with new question and answers found between {} and {}".format(len(briefs), start_date, end_date)
    )

    # find the IDs of interested suppliers {supplier_id: [briefid1, briefid2]}
    interested_suppliers = get_ids_of_interested_suppliers_for_briefs(data_api_client, briefs)
    interested_suppliers = dict(
        (supplier_id, briefs) for supplier_id, briefs in interested_suppliers.iteritems()
        if supplier_id not in exclude_supplier_ids
    )
    logger.info(
        "{} suppliers found interested in these briefs".format(len(interested_suppliers))
    )

    for supplier_id, brief_ids in interested_suppliers.items():
        # Get the brief objects for this supplier
        supplier_briefs = filter(lambda b: b['id'] in brief_ids, briefs)
        # get a context for each supplier email
        supplier_context = create_context_for_supplier(stage, supplier_briefs)
        email_addresses = get_supplier_email_addresses_by_supplier_id(data_api_client, supplier_id)
        if dry_run:
            logger.info(
                "Would notify supplier ID {supplier_id} for brief IDs {brief_ids_list}",
                extra={
                    'supplier_id': supplier_id,
                    'brief_ids_list': ", ".join(map(str, brief_ids))
                }
            )
        else:
            logger.info(
                "Notifying supplier ID {supplier_id} of new questions/answers for brief IDs {brief_ids_list}",
                extra={
                    'supplier_id': supplier_id,
                    'brief_ids_list': ", ".join(map(str, brief_ids))
                }
            )
            send_supplier_emails(email_api_key, email_addresses, supplier_context, logger)

    return True
