from datetime import datetime
from dmutils.formats import DATE_FORMAT, DATETIME_FORMAT


format_datetime_string_as_date = lambda x: datetime.strptime(x, DATETIME_FORMAT).strftime(DATE_FORMAT) if x else None
remove_username_from_email_address = lambda x: '{}'.format(x.split('@').pop()) if x else None
