import datetime
from typing import Optional

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DEFAULT_DATETIME = "1970-01-01T00:00:00.000000Z"


def audit_date(
    from_date: Optional[datetime.date] = None,
    to_date: Optional[datetime.date] = None
) -> Optional[str]:
    """Returns a string acceptable to the find_audit_events `audit-date` parameter

    >>> audit_date(from_date=datetime.date(year=2020, month=9, day=28))
    '>=2020-09-28'
    >>> audit_date(to_date=datetime.date(year=2020, month=10, day=28))
    '<2020-10-28'
    >>> audit_date(
    ...     from_date=datetime.date(year=2020, month=9, day=28),
    ...     to_date=datetime.date(year=2020, month=10, day=28),
    ... )
    '2020-09-28..2020-10-28'
    """
    format_spec = "%Y-%m-%d"
    if from_date and not to_date:
        return f">={from_date:{format_spec}}"
    elif to_date and not from_date:
        return f"<{to_date:{format_spec}}"
    elif from_date and to_date:
        return f"{from_date:{format_spec}}..{to_date:{format_spec}}"
    else:
        return None


def parse_datetime(s: str) -> datetime.datetime:
    """Parse a datetime from a string that might not include all of the datetime parts

    >>> parse_datetime('2020-10')
    datetime.datetime(2020, 10, 1, 0, 0)
    """
    try:
        return datetime.datetime.strptime(s, ISO_FORMAT)
    except ValueError as e:
        if len(s) < len(DEFAULT_DATETIME):
            return datetime.datetime.strptime(s + DEFAULT_DATETIME[len(s):], ISO_FORMAT)
        else:
            raise e
