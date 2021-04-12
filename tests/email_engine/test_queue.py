# this file needs a lot of long lines because we are testing examples of logfiles
# flake8: noqa E501

from textwrap import dedent
from unittest import mock

import pytest

from notifications_python_client.errors import APIError

from dmscripts.email_engine.queue import EmailNotification, LoggingQueue, run


class TestRun:
    @pytest.fixture
    def queue(self):
        queue = LoggingQueue()
        with mock.patch("dmscripts.email_engine.queue.LoggingQueue") as constructor:
            constructor.return_value = queue
            yield queue

    @pytest.fixture
    def logfile(self, tmp_path):
        logfile = tmp_path / "log.txt"
        logfile.touch()
        return logfile

    def test_run(self, notifications_generator, send_notification, logfile, queue):
        run(send_notification, notifications=notifications_generator(), logfile=logfile)

        assert len(queue.todo) == 0
        assert len(queue.done) == 10

    def test_run_with_logfile(self, send_notification, logfile, queue):
        logfile.write_text(
            dedent(
                """\
                queue update: queued notification {"email_address": "hello@example.com", "template_id": "0000-0001"}
                queue update: queued notification {"email_address": "test@example.com", "template_id": "0000-0002"}
                queue update: generator is exhausted, read 2 notifications into queue
                queue update: send notification {"email_address": "hello@example.com", "template_id": "0000-0001"} response {"id": "1001-1000"}
                """
            )
        )

        run(send_notification, notifications=[], logfile=logfile)

        assert len(queue.todo) == 0
        assert len(queue.done) == 2

    def test_run_aborts_if_generator_was_not_exhausted_in_logfile(self, logfile):
        logfile.write_text(
            dedent(
                """\
                queue update: queued notification {"email_address": "hello@example.com", "template_id": "0000-0001"}
                queue update: queued notification {"email_address": "test@example.com", "template_id": "0000-0002"}
                """
            )
        )

        with pytest.raises(RuntimeError):
            run(mock.Mock(), notifications=[], logfile=logfile)

    def test_run_logs_remaining_todo_if_interrupted_by_exception(
        self, caplog, notifications_generator, logfile, crashing_send_notification
    ):
        send_notification = crashing_send_notification(
            crash_after=3, crash_with=APIError(message="woops")
        )

        with pytest.raises(APIError):
            run(
                send_notification,
                notifications=notifications_generator(),
                logfile=logfile,
            )

        assert (
            caplog.messages[-1]
            == "sending emails was stopped by APIError with 7 notifications left to send"
        )


class TestLoggingQueue:
    def test_put(self):
        queue = LoggingQueue()

        queue.put(
            EmailNotification(
                email_address="hello@example.com", template_id="0000-000a"
            )
        )

        assert len(queue.todo) == 1

    def test_put_logs_notification(self, caplog):
        queue = LoggingQueue()

        queue.put(
            EmailNotification(
                email_address="hello@example.com", template_id="0000-000a"
            )
        )

        assert caplog.messages[-1] == (
            "queue update: queued notification {'email_address': 'hello@example.com', 'template_id': '0000-000a', 'personalisation': None}"
        )

    def test_put_does_not_add_duplicate_notifications(self, caplog):
        queue = LoggingQueue()

        queue.put(
            EmailNotification(
                email_address="hello@example.com", template_id="0000-000a"
            )
        )
        queue.put(
            EmailNotification(
                email_address="hello@example.com", template_id="0000-000a"
            )
        )

        assert caplog.messages[-1] == (
            "ignoring duplicate notification {'email_address': 'hello@example.com', 'template_id': '0000-000a', 'personalisation': None}"
        )
        assert len(queue.todo) == 1

    def test_send_next(self, send_notification):
        queue = LoggingQueue()

        queue.put(
            EmailNotification(
                email_address="hello@example.com", template_id="0000-000a"
            )
        )

        queue.send_next(send_notification)

        assert len(queue.todo) == 0
        assert len(queue.done) == 1

    def test_send_next_logs_notification_and_response(self, caplog, send_notification):
        queue = LoggingQueue()

        queue.put(
            EmailNotification(
                email_address="hello@example.com", template_id="0000-000a"
            )
        )

        queue.send_next(lambda x: {"id": "cafe"})

        assert caplog.messages[-1] == (
            "queue update: send notification {'email_address': 'hello@example.com', 'template_id': '0000-000a', 'personalisation': None} response {'id': 'cafe'}"
        )

    def test_read_log(self):
        loglines = """
            2021-04-08T10:42:00Z queue update: queued notification {"email_address": "hello@example.com", "template_id": "0000-0001"}
            2021-04-08T10:42:00Z queue update: queued notification {"email_address": "test@example.com", "template_id": "0000-0002"}
            2021-04-08T10:43:05Z boring log line about things not queue related
            2021-04-08T10:44:10Z queue update: send notification {"email_address": "hello@example.com", "template_id": "0000-0001"} response {"id": "1001-1000"}
        """

        queue = LoggingQueue()
        queue._read_log(loglines.splitlines())

        assert list(queue.todo) == [
            EmailNotification(template_id="0000-0002", email_address="test@example.com")
        ]
        assert queue.done == {
            EmailNotification(
                template_id="0000-0001", email_address="hello@example.com"
            ): {"id": "1001-1000"}
        }

    def test_read_log_returns_true_if_original_generator_was_exhausted(self):
        queue = LoggingQueue()
        _, exhausted = queue._read_log(
            ["queue update: generator is exhausted, read 0 notifications into queue"]
        )
        assert exhausted is True

    def test_read_log_returns_false_if_original_generator_was_not_exhausted(self):
        queue = LoggingQueue()
        _, exhausted = queue._read_log(
            [
                "queue update: queued notification {'email_address': 'test@example.com', 'template_id': 'a'}"
            ]
        )
        assert exhausted is False

    @pytest.mark.parametrize(
        "invalid_loglines",
        (
            # out of order lines
            """
            queue update: send notification {"email_address": "hello@example.com", "template_id": "0000-0001"} response {"id": "1001-1000"}
            queue update: queued notification {"email_address": "hello@example.com", "template_id": "0000-0001"}
            """,
            # missing lines
            """
            queue update: send notification {"email_address": "hello@example.com", "template_id": "0000-0001"} response {"id": "1001-1000"}
            """,
            # line that has typo
            """
            queue update: sned notification {"email_address": "hello@example.com", "template_id": "0000-0001"} response {"id": "1001-1000"}
            """,
        ),
    )
    def test_read_state_raises_error_if_log_has_invalid_lines(self, invalid_loglines):
        queue = LoggingQueue()
        with pytest.raises(RuntimeError):
            queue._read_log(invalid_loglines.splitlines())

    def test_put_from_logfile(self, tmp_path):
        log_file = tmp_path / "log.txt"

        log_file.write_text(
            """2021-04-08T10:42:00Z queue update: queued notification {"email_address": "hello@example.com", "template_id": "0000-0001"}\n"""
        )

        queue = LoggingQueue()
        queue.put_from_logfile(log_file)

        assert list(queue.todo) == [
            EmailNotification(
                template_id="0000-0001", email_address="hello@example.com"
            )
        ]

    def test_put_from_generator(self, notifications_generator):
        queue = LoggingQueue()
        queue.put_from(notifications_generator())

    def test_put_from_logs_when_generator_is_exhausted(
        self, caplog, notifications_generator
    ):
        queue = LoggingQueue()
        queue.put_from(notifications_generator())

        assert caplog.messages[-1] == (
            "queue update: generator is exhausted, read 10 notifications into queue"
        )

    def test_put_from_logs_roundtrip_with_read_log(
        self, caplog, send_notification, notifications_generator
    ):
        notifications = list(notifications_generator())

        queue_a = LoggingQueue()
        queue_a.put_from(notifications)

        assert list(queue_a.todo) == notifications

        for _ in range(2):
            queue_a.send_next(send_notification)

        queue_b = LoggingQueue()
        queue_b._read_log(caplog.text.splitlines())

        assert queue_b.todo == queue_a.todo
        assert queue_b.done == queue_a.done
