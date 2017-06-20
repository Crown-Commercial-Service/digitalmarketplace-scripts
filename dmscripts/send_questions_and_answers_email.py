import dmapiclient

from datetime import datetime, date, timedelta

from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging
from dmutils.formats import DATETIME_FORMAT


logger = logging_helpers.configure_logger({'dmapiclient': logging.INFO})


def get_live_briefs_with_new_questions_and_answers_between_two_dates(data_api_client, start_date, end_date):
    briefs = data_api_client.find_briefs_iter(status='live', human=True)

    # return a list of briefs that contain clarification questions published between the start data and the end date
    return [brief for brief in briefs if len(brief['clarificationQuestions']) and any(
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

    return interested_suppliers


def main(data_api_client, number_of_days):
    logger.info("Begin to send brief update notification emails")

    # get today at 8 in the morning
    end_date = datetime.utcnow().replace(hour=8, minute=0, second=0, microsecond=0)
    # get yesterday at 8 in the morning
    start_date = end_date - timedelta(days=number_of_days)

    # we need to find the briefs
    briefs = get_live_briefs_with_new_questions_and_answers_between_two_dates(data_api_client, start_date, end_date)

    # we want to find all questions and answers that were submitted between start and end dates

    # look for people who have asked clarification questions
    # data_api_client.find_audit_events(
    # audit_type=dmapiclient.audit.AuditTypes.send_clarification_question, audit_date=start_date.strftime('%Y-%m-%d'))
