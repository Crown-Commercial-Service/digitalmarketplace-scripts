from dmapiclient import DataAPIClient as data_api_client
from datetime import datetime, date, timedelta


def get_brief_responses(data_api_client, brief):
    return data_api_client.find_brief_responses(brief_id=brief["id"], status="submitted").get("briefResponses")


def get_withdrawn_briefs_with_responses(data_api_client, withdrawn_briefs):
    return {brief["id"]: get_brief_responses(data_api_client, brief) for brief in withdrawn_briefs}


def main(data_api_client):
    withdrawn_date = date.today() - timedelta(days=1)
    briefs_withdrawn_on_date = data_api_client.find_briefs(withdrawn_on=withdrawn_date).get("briefs")
    withdrawn_briefs_with_responses = get_withdrawn_briefs_with_responses(data_api_client, briefs_withdrawn_on_date)
    return True
