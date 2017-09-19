from datetime import datetime
from dmutils.formats import DATETIME_FORMAT


def get_briefs_closed_on_date(data_api_client, date_closed):
    return [
        brief for brief in data_api_client.find_briefs_iter(status='closed', with_users=True)
        if datetime.strptime(brief['applicationsClosedAt'], DATETIME_FORMAT).date() == date_closed
    ]
