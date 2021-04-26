from collections.abc import Hashable

import pytest

from dmscripts.email_engine.typing import EmailNotification


class TestEmailNotification:
    def test_is_hashable(self):
        isinstance(EmailNotification, Hashable)

        assert hash(
            EmailNotification(
                email_address="hello@example.com",
                template_id="0000-0000",
                personalisation={"name": "Hello"},
            )
        )

    def test_is_comparable(self):
        a = EmailNotification(
            email_address="hello@example.com",
            template_id="0000-0000",
            personalisation={"name": "Hello"},
        )
        b = EmailNotification(
            template_id="0000-0000",
            email_address="hello@example.com",
            personalisation={"name": "Hello"},
        )
        c = EmailNotification(
            email_address="different@example.com",
            template_id="0000-0001",
            personalisation={"name": "Hello"},
        )

        assert id(a) != id(b) != id(c)

        assert a == b

        assert a != c
        assert b != c

    def test_is_frozen(self):
        a = EmailNotification(
            email_address="hello@example.com",
            template_id="0000-0000",
            personalisation={"name": "Hello"},
        )

        with pytest.raises(RuntimeError):
            a["email_address"] = "hello1@example.com"

    def test_str_notification_can_be_parsed_using_from_str(self):
        a = EmailNotification(
            email_address="hello@example.com",
            template_id="0000-0000",
            personalisation={"name": "Hello"},
        )

        b = EmailNotification.from_str(str(a))

        assert a == b
