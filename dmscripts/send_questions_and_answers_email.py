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


def get_id_of_suppliers_who_started_applying(data_api_client, list_of_briefs):
    suppliers_who_started_applying_by_brief = {}
    for brief in list_of_briefs:
        responses = data_api_client.find_brief_responses(brief_id=brief["id"])
        supplier_ids = [response["supplierId"] for response in responses["briefResponses"]]
        suppliers_who_started_applying_by_brief[brief["id"]] = supplier_ids
    return suppliers_who_started_applying_by_brief


def main(data_api_client, number_of_days):
    logger.info("Begin to send brief update notification emails")

    # get today at 8 in the morning
    end_date = datetime.utcnow().replace(hour=8, minute=0, second=0, microsecond=0)
    # get yesterday at 8 in the morning
    start_date = end_date - timedelta(days=number_of_days)

    briefs = get_live_briefs_with_new_questions_and_answers_between_two_dates(data_api_client, start_date, end_date)

    # we need to find the briefs
    # we want to find all questions and answers that were submitted between start and end dates

    # look for people who have asked clarification questions
    # data_api_client.find_audit_events(
    # audit_type=dmapiclient.audit.AuditTypes.send_clarification_question, audit_date=start_date.strftime('%Y-%m-%d'))
