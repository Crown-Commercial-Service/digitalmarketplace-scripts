from datetime import datetime, timedelta
from dmutils.formats import DATE_FORMAT


def get_date_closed(date_closed):
    """
    :param date_closed: YYYY-MM-DD string supplied via script argument
    :return: Python datetime object
    """
    if date_closed is None:
        return (datetime.utcnow() - timedelta(days=1)).date()
    else:
        return datetime.strptime(date_closed, DATE_FORMAT).date()
