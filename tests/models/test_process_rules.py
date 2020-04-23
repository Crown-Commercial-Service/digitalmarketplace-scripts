import pytest

from dmscripts.models.process_rules import (
    format_datetime_string_as_date,
    remove_username_from_email_address
)


class TestFormatDatetimeStringAsDate:

    def test_format_datetime_string_as_date(self):
        initial_date = "2016-10-08T12:00:00.00000Z"
        formatted_date = "2016-10-08"
        assert format_datetime_string_as_date(initial_date) == formatted_date

    def test_format_datetime_string_as_date_raises_error_if_initial_date_format_incorrect(self):
        initial_dates = (
            "2016-10-08T12:00:00.00000",
            "2016-10-08T12:00:00",
            "2016-10-08"
        )
        for date in initial_dates:
            with pytest.raises(ValueError) as excinfo:
                format_datetime_string_as_date(date)

            assert "time data '{}' does not match format".format(date) in str(excinfo.value)


class TestRemoveUsernameFromEmailAddress:

    def test_remove_username_from_email_address(self):
        initial_email_address = "user.name@domain.com"
        formatted_email_address = "domain.com"
        assert remove_username_from_email_address(initial_email_address) == formatted_email_address
