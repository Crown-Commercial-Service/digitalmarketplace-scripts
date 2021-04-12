from unittest import mock

import pytest

from dmscripts.email_engine.cli import argument_parser_factory
from dmscripts.email_engine.typing import EmailNotification


@pytest.fixture
def caplog(caplog):
    with caplog.at_level(15):
        yield caplog


@pytest.fixture
def default_argument_parser_factory():
    """Patch email_engine's argument_parser_factory so that it will not require any arguments"""

    def factory(*args, **kwargs):
        return argument_parser_factory(
            *args,
            **kwargs,
            notify_api_key_required=False,
            notify_template_id_required=False,
            stage_required=False,
        )

    with mock.patch("dmscripts.email_engine.cli.argument_parser_factory", factory):
        with mock.patch("dmscripts.email_engine.argument_parser_factory", factory):
            with mock.patch("sys.argv", ["email_engine"]):
                yield factory


@pytest.fixture
def notifications_generator():
    def g(*args, **kwargs):
        for i in range(10):
            yield EmailNotification(
                email_address=f"{i}@example.com", template_id="0000-0003"
            )

    return mock.Mock(wraps=g)


@pytest.fixture
def send_notification():
    def f(*args, **kwargs):
        return {"id": str(id((args, kwargs)))}

    return mock.Mock(wraps=f)


@pytest.fixture
def crashing_send_notification(send_notification):
    def factory(crash_after: int, crash_with=RuntimeError):
        countdown = crash_after

        def crasher(*args, **kwargs):
            nonlocal countdown
            countdown -= 1
            if countdown == 0:
                raise crash_with
            return send_notification(*args, **kwargs)

        return crasher

    return factory
