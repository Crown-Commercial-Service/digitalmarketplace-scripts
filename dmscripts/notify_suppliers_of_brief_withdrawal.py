from dmutils.email.helpers import hash_string
from dmutils.env_helpers import get_web_url_from_stage


def get_brief_response_emails(data_api_client, brief_id):
    responses = data_api_client.find_brief_responses_iter(brief_id=brief_id, status="submitted")
    return [response["respondToEmailAddress"] for response in responses]


def create_context_for_brief(stage, brief):
    return {
        'brief_title': brief['title'],
        'brief_link': '{}/{}/opportunities/{}'.format(
            get_web_url_from_stage(stage),
            brief['frameworkFramework'],
            brief['id']
        )
    }


def main(data_api_client, mail_client, template_id, stage, logger, withdrawn_date, brief_id=None, dry_run=False):

    withdrawn_briefs = data_api_client.find_briefs_iter(status='withdrawn', withdrawn_on=withdrawn_date)

    if brief_id:
        withdrawn_briefs = filter(lambda i: i['id'] == brief_id, withdrawn_briefs)

    for brief in withdrawn_briefs:
        email_addresses = get_brief_response_emails(data_api_client, brief['id'])
        if not email_addresses:
            continue

        brief_email_context = create_context_for_brief(stage, brief)
        for email_address in email_addresses:
            if not dry_run:
                mail_client.send_email(
                    email_address, template_id, brief_email_context, allow_resend=False
                )
            logger.info(
                "%sEMAIL: Withdrawal of Brief ID: %d to %s",
                '[Dry-run]' if dry_run else '',
                brief['id'],
                hash_string(email_address),
            )
    return True
