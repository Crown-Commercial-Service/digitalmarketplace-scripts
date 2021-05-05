# this file needs a lot of long lines because we are testing examples of logfiles
# flake8: noqa E501
import sys
from unittest import mock

import pytest

from dmscripts.email_engine import EmailNotification, email_engine


pytestmark = pytest.mark.usefixtures("default_argument_parser_factory")


class TestEmailEngine:
    @pytest.fixture(autouse=True)
    def notifications_api_client(self):
        with mock.patch(
            "dmscripts.email_engine.NotificationsAPIClient", autospec=True
        ) as NotificationsAPIClient:
            with mock.patch.dict("os.environ", {"DM_NOTIFY_API_KEY": "test-api-key"}):
                yield NotificationsAPIClient

    @pytest.fixture
    def logfile(self, tmp_path):
        return tmp_path / "log.txt"

    def test_email_engine(self, caplog, notifications_api_client, logfile):
        def notifications_generator(**kwargs):
            yield EmailNotification(
                email_address="test1@example.com",
                template_id="000-001",
                personalisation={"name": "test1"},
            )
            yield EmailNotification(
                email_address="test2@example.com",
                template_id="000-001",
                personalisation={"name": "test2"},
            )

        notifications_generator = mock.Mock(wraps=notifications_generator)

        with mock.patch.object(sys, 'argv', ['--reference=test_email_engine']):
            email_engine(
                notifications_generator,
                argv=[],
                reference="test_email_engine",
                logfile=logfile,
            )

        assert notifications_generator.called
        assert notifications_api_client.call_args == mock.call("test-api-key")
        assert notifications_api_client(
            "test-api-key"
        ).send_email_notification.call_args_list == [
            mock.call(
                email_address="test1@example.com",
                template_id="000-001",
                personalisation={"name": "test1"},
                reference="test_email_engine-giOMmd3dhc52GqVUTRNFoXDGIfAeC5wLZFnPV9rM5L4=",
            ),
            mock.call(
                email_address="test2@example.com",
                template_id="000-001",
                personalisation={"name": "test2"},
                reference="test_email_engine-bVPjXSd-Joerdai08PbodN0WxjLvWhRaOgiehCsIXew=",
            ),
        ]
        

        caplog.messages[
            -1
        ] == "sent 2 email notifications with reference test_email_engine"

    def test_email_engine_resume(
        self,
        caplog,
        notifications_api_client,
        logfile,
        notifications_generator,
        crashing_send_notification,
        send_notification,
    ):
        notifications_api_client(
            "test_api_key"
        ).send_email_notification = crashing_send_notification(crash_after=3)

        with pytest.raises(RuntimeError):
            email_engine(
                notifications_generator,
                argv=[],
                reference="test_email_engine_resume",
                logfile=logfile,
            )

        notifications_api_client(
            "test_api_key"
        ).send_email_notification = send_notification

        email_engine(
            notifications_generator,
            argv=[],
            reference="test_email_engine_resume",
            logfile=logfile,
        )

        caplog.messages[
            -1
        ] == "sent 10 email notifications with reference test_email_engine"

    def test_email_engine_logfile(self, notifications_api_client, logfile):
        def notifications_generator(**args):
            yield EmailNotification(
                email_address="test1@example.com",
                template_id="000-001",
                personalisation={"name": "test1"},
            )
            yield EmailNotification(
                email_address="test2@example.com",
                template_id="000-001",
                personalisation={"name": "test2"},
            )

        notifications_api_client(
            "test_api_key"
        ).send_email_notification.return_value = {}

        with mock.patch.object(sys, 'argv', ['--reference=test_email_engine_logfile']):
            email_engine(
                notifications_generator,
                argv=[],
                reference="test_email_engine_logfile",
                logfile=logfile,
            )

        loglines = logfile.read_text().splitlines()
        assert loglines == [
            "OFFICIAL SENSITIVE - do not distribute - this file contains email addresses and other PII",
            "getting notifications to send from API",
            "queue update: queued notification {'email_address': 'test1@example.com', 'template_id': '000-001', 'personalisation': {'name': 'test1'}}",
            "queue update: queued notification {'email_address': 'test2@example.com', 'template_id': '000-001', 'personalisation': {'name': 'test2'}}",
            "queue update: generator is exhausted, read 2 notifications into queue",
            "queue update: send notification {'email_address': 'test1@example.com', 'template_id': '000-001', 'personalisation': {'name': 'test1'}} response {}",
            "queue update: send notification {'email_address': 'test2@example.com', 'template_id': '000-001', 'personalisation': {'name': 'test2'}} response {}",
            "sent 2 email notifications with reference test_email_engine_logfile",
        ]
