from datetime import datetime, date
from typing import Union

from dmutils.formats import DATE_FORMAT


def get_briefs_closed_on_date(data_api_client, date_closed: Union[datetime, date]):
    return list(
        data_api_client.find_briefs_iter(status='closed', with_users=True, closed_on=date_closed.strftime(DATE_FORMAT)))
