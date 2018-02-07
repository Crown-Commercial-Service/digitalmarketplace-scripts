from datetime import datetime, timedelta

from dmutils.email.exceptions import EmailError
from dmutils.email.helpers import hash_string
from dmutils.formats import DATE_FORMAT
from dmscripts.helpers import env_helpers


def _create_context_for_brief(stage, brief):
    return {
        'brief_title': brief['title'],
        'brief_link': '{}/{}/opportunities/{}'.format(
            env_helpers.get_web_url_from_stage(stage),
            brief['framework']['family'],
            brief['id']
        )
    }


def _get_brief_responses_to_be_notified(data_api_client, brief_response_ids, awarded_at):
    brief_responses = []

    if brief_response_ids:
        # Used for re-running failed email sending
        for brief_response_id in brief_response_ids:
            brief_responses.append(data_api_client.get_brief_response(brief_response_id)['briefResponses'])
    else:
        awarded_at_date = awarded_at or (datetime.utcnow() - timedelta(days=1)).strftime(DATE_FORMAT)
        awarded_brief_responses = data_api_client.find_brief_responses_iter(awarded_at=awarded_at_date)

        for abr in awarded_brief_responses:
            # Add the successful BriefResponse
            brief_responses.append(abr)
            # Get the unsuccessful BriefResponses
            submitted_brief_responses = data_api_client.find_brief_responses_iter(
                brief_id=abr['briefId'], status='submitted'
            )
            brief_responses.extend(submitted_brief_responses)

    return brief_responses


def _build_and_send_emails(brief_responses, mail_client, stage, dry_run, template_id, logger):
    failed_brief_responses = []

    # Now email everyone whose Brief got awarded
    for brief_response in brief_responses:
        email_address = brief_response["respondToEmailAddress"]
        if not email_address:
            continue

        brief_email_context = _create_context_for_brief(stage, brief_response['brief'])
        try:
            if not dry_run:
                mail_client.send_email(
                    email_address, template_id, brief_email_context, allow_resend=False
                )
            logger.info(
                "{dry_run}EMAIL: Award of Brief Response ID: {brief_response_id} to {email_address}",
                extra={
                    'dry_run': '[Dry-run] - ' if dry_run else '',
                    'brief_response_id': brief_response['id'],
                    'email_address': hash_string(email_address),
                }
            )
        except EmailError:
            # Log individual failures in more detail
            logger.error(
                "Email sending failed for BriefResponse {brief_response_id} (Brief ID {brief_id})",
                extra={
                    "brief_id": brief_response['brief']['id'],
                    "brief_response_id": brief_response['id']
                }
            )
            failed_brief_responses.append(brief_response['id'])

    return failed_brief_responses


def main(
    data_api_client, mail_client, template_id, stage, logger,
    dry_run=False, brief_response_ids=None, awarded_at=None
):
    brief_responses = _get_brief_responses_to_be_notified(data_api_client, brief_response_ids, awarded_at)

    failed_brief_responses = _build_and_send_emails(brief_responses, mail_client, stage, dry_run, template_id, logger)

    # Log a summary of failures at the end of the job
    if failed_brief_responses:
        logger.error(
            "Email sending failed for the following {count} BriefResponses: {brief_response_ids}",
            extra={
                "brief_response_ids": ",".join(map(str, failed_brief_responses)),
                "count": len(failed_brief_responses)
            }
        )
        return False

    return True
