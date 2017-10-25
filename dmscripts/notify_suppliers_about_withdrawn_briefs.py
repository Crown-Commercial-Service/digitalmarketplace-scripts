from dmapiclient import DataAPIClient as data_api_client
from datetime import datetime, date, timedelta
from dmscripts.helpers import env_helpers


def get_brief_response_emails(data_api_client, brief):
    responses = data_api_client.find_brief_responses(brief_id=brief["id"], status="submitted").get("briefResponses")
    return [response["respondToEmailAddress"] for response in responses]


def get_withdrawn_briefs_with_responses(data_api_client, withdrawn_briefs):
    return [(brief, get_brief_response_emails(data_api_client, brief)) for brief in withdrawn_briefs]

def create_context_for_brief(stage, brief):
    return {
        'brief_title': brief['title'],
        'brief_link': '{0}/{1}/opportunities/{2}'.format(
            env_helpers.get_web_url_from_stage(stage),
            brief['frameworkFramework'],
            brief['id']
        )
    }

def main(data_api_client):
    withdrawn_date = date.today() - timedelta(days=1)
    briefs_withdrawn_on_date = data_api_client.find_briefs(withdrawn_on=withdrawn_date).get("briefs")
    withdrawn_briefs_with_responses = get_withdrawn_briefs_with_responses(data_api_client, briefs_withdrawn_on_date)
    # for brief, email_addresses in withdrawn_briefs_with_responses:
    #     brief_context = create_context_for_brief(stage, brief)
    #     for email_address in email_addresses:
    #         #send_email()
    return True
