import pytest
import logging
import mock
import uuid

from freezegun import freeze_time

from dmapiclient import DataAPIClient
from dmtestutils.api_model_stubs import FrameworkStub, SupplierFrameworkStub
from dmtestutils.comparisons import AnyStringMatching
from dmutils.email import DMNotifyClient, EmailError

from dmscripts.notify_suppliers_of_framework_application_event import \
    notify_suppliers_of_framework_application_event


_supplier_frameworks = (
    SupplierFrameworkStub(supplier_id=303132, framework_slug="g-cloud-99").response(),
    SupplierFrameworkStub(supplier_id=303233, framework_slug="g-cloud-99").response(),
    SupplierFrameworkStub(supplier_id=303133, framework_slug="g-cloud-99").response(),
    SupplierFrameworkStub(supplier_id=313233, framework_slug="g-cloud-99").response(),
)


_supplier_users_by_supplier = {
    supplier_id: tuple({"supplierId": supplier_id, **supplier} for supplier in suppliers)
    for supplier_id, suppliers in (
        (303132, (
            {
                "id": 56,
                "emailAddress": "one@peasoup.net",
                "active": True,
            },
            {
                "id": 57,
                "emailAddress": "two@peasoup.net",
                "active": True,
            },
        )),
        (303233, ()),
        (303133, (
            {
                "id": 58,
                "emailAddress": "one@bubbling-suds.org",
                "active": False,
            },
        )),
        (313233, (
            {
                "id": 59,
                "emailAddress": "one@shirts.co.ua",
                "active": False,
            },
            {
                "id": 60,
                "emailAddress": "two@shirts.co.ua",
                "active": True,
            },
            {
                "id": 61,
                "emailAddress": "three@shirts.co.ua",
                "active": True,
            },
        )),
    )
}


class TestNotifySuppliersOfFrameworkApplicationEvent:

    def setup(self):
        # Set up DMAPIClient
        self.mock_data_api_client = mock.create_autospec(DataAPIClient, instance=True)
        framework_response = FrameworkStub(
            slug="g-cloud-99",
            status="open",
        ).single_result_response()
        framework_response["frameworks"]["intentionToAwardAtUTC"] = "2000-06-29T16:00:00.0000Z"
        framework_response["frameworks"]["frameworkLiveAtUTC"] = "2000-06-29T16:30:00.0000Z"
        self.mock_data_api_client.get_framework.return_value = framework_response
        self.mock_data_api_client.find_framework_suppliers_iter.side_effect = lambda *a, **k: iter(_supplier_frameworks)
        self.mock_data_api_client.find_users_iter.side_effect = lambda *a, **k: iter(
            _supplier_users_by_supplier[k["supplier_id"]]
        )

        # Setup DMNotifyClient
        self.mock_notify_client = mock.create_autospec(DMNotifyClient, instance=True)
        self.mock_notify_client.get_reference.side_effect = lambda *a: ",".join(str(x) for x in a)
        self.mock_notify_client.has_been_sent.side_effect = (
            # this one ref is considered to be already sent
            lambda reference: reference == (
                "two@shirts.co.ua,8877eeff,{'framework_slug': 'g-cloud-99', 'run_id': "
                "'00010203-0405-0607-0809-0a0b0c0d0e0f'}"
            )
        )

        # Setup logger
        self.mock_logger = mock.create_autospec(logging.Logger, instance=True)

        # Setup expected calls
        self.expected_context = {
            'framework_name': 'G-Cloud 99',
            'updates_url': 'https://www.digitalmarketplace.service.gov.uk/suppliers/frameworks/g-cloud-99/updates',
            'framework_dashboard_url': 'https://www.digitalmarketplace.service.gov.uk/suppliers/frameworks/g-cloud-99/',
            'clarification_questions_closed': 'no',
            'clarificationsCloseAt_displaytimeformat': '12:00am GMT',
            'clarificationsCloseAt_dateformat': 'Saturday 1 January 2000',
            'clarificationsCloseAt_datetimeformat': 'Saturday 1 January 2000 at 12:00am GMT',
            'clarificationsPublishAt_displaytimeformat': '12:00am GMT',
            'clarificationsPublishAt_dateformat': 'Sunday 2 January 2000',
            'clarificationsPublishAt_datetimeformat': 'Sunday 2 January 2000 at 12:00am GMT',
            'applicationsCloseAt_displaytimeformat': '12:00am GMT',
            'applicationsCloseAt_dateformat': 'Monday 3 January 2000',
            'applicationsCloseAt_datetimeformat': 'Monday 3 January 2000 at 12:00am GMT',
            'intentionToAwardAt_displaytimeformat': '5:00pm BST',
            'intentionToAwardAt_timetoday': 'Today at 5pm BST',
            'intentionToAwardAt_dateformat': 'Thursday 29 June 2000',
            'intentionToAwardAt_datetimeformat': 'Thursday 29 June 2000 at 5:00pm BST',
            'frameworkLiveAt_displaytimeformat': '5:30pm BST',
            'frameworkLiveAt_dateformat': 'Thursday 29 June 2000',
            'frameworkLiveAt_datetimeformat': 'Thursday 29 June 2000 at 5:30pm BST',
            # no frameworkLiveAt_timetoday because it's non-hour-exact
            'frameworkExpiresAt_displaytimeformat': '12:00am GMT',
            'frameworkExpiresAt_dateformat': 'Thursday 6 January 2000',
            'frameworkExpiresAt_datetimeformat': 'Thursday 6 January 2000 at 12:00am GMT',
        }

    @pytest.mark.parametrize("dry_run", (False, True))
    @mock.patch("dmscripts.notify_suppliers_of_framework_application_event.uuid4")
    def test_happy_path_without_resume_run_id(self, mock_uuid4, dry_run):
        mock_uuid4.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")

        with freeze_time('2000-06-29 02:55:55'):
            assert notify_suppliers_of_framework_application_event(
                data_api_client=self.mock_data_api_client,
                notify_client=self.mock_notify_client,
                notify_template_id="8877eeff",
                framework_slug="g-cloud-99",
                dry_run=dry_run,
                stage="production",
                logger=self.mock_logger,
                run_id=None,
            ) == 0

        expected_run_id = "12345678-1234-5678-1234-567812345678"

        assert mock_uuid4.mock_calls == [mock.call()]
        assert self.mock_data_api_client.mock_calls == [
            mock.call.get_framework("g-cloud-99"),
            mock.call.find_framework_suppliers_iter("g-cloud-99"),
            mock.call.find_users_iter(supplier_id=303132),
            mock.call.find_users_iter(supplier_id=303233),
            mock.call.find_users_iter(supplier_id=303133),
            mock.call.find_users_iter(supplier_id=313233),
        ]
        assert self.mock_notify_client.mock_calls == [
            mock.call.get_reference("one@peasoup.net", "8877eeff", {
                'framework_slug': 'g-cloud-99',
                'run_id': expected_run_id,
            }),
            (mock.call.has_been_sent(
                f"one@peasoup.net,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}"
            ) if dry_run else mock.call.send_email(
                'one@peasoup.net',
                '8877eeff',
                self.expected_context,
                allow_resend=False,
                reference=f"one@peasoup.net,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}",
            )),
            mock.call.get_reference("two@peasoup.net", "8877eeff", {
                'framework_slug': 'g-cloud-99',
                'run_id': expected_run_id,
            }),
            (mock.call.has_been_sent(
                f"two@peasoup.net,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}",
            ) if dry_run else mock.call.send_email(
                'two@peasoup.net',
                '8877eeff',
                self.expected_context,
                allow_resend=False,
                reference=f"two@peasoup.net,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}",
            )),
            mock.call.get_reference("two@shirts.co.ua", "8877eeff", {
                'framework_slug': 'g-cloud-99',
                'run_id': expected_run_id,
            }),
            (mock.call.has_been_sent(
                f"two@shirts.co.ua,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}",
            ) if dry_run else mock.call.send_email(
                'two@shirts.co.ua',
                '8877eeff',
                self.expected_context,
                allow_resend=False,
                reference=f"two@shirts.co.ua,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}",
            )),
            mock.call.get_reference("three@shirts.co.ua", "8877eeff", {
                'framework_slug': 'g-cloud-99',
                'run_id': expected_run_id,
            }),
            (mock.call.has_been_sent(
                f"three@shirts.co.ua,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}",
            ) if dry_run else mock.call.send_email(
                'three@shirts.co.ua',
                '8877eeff',
                self.expected_context,
                allow_resend=False,
                reference=f"three@shirts.co.ua,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}",
            )),
        ]

    @pytest.mark.parametrize("dry_run", (False, True))
    @mock.patch("dmscripts.notify_suppliers_of_framework_application_event.uuid4")
    def test_happy_paths_with_resume_run_id(self, mock_uuid4, dry_run):
        run_id = uuid.UUID("00010203-0405-0607-0809-0a0b0c0d0e0f")
        mock_uuid4.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")

        with freeze_time('2000-06-29 02:55:55'):
            assert notify_suppliers_of_framework_application_event(
                data_api_client=self.mock_data_api_client,
                notify_client=self.mock_notify_client,
                notify_template_id="8877eeff",
                framework_slug="g-cloud-99",
                dry_run=dry_run,
                stage="production",
                logger=self.mock_logger,
                run_id=run_id,
            ) == 0

        expected_run_id = str(run_id)

        assert mock_uuid4.mock_calls == []
        assert self.mock_data_api_client.mock_calls == [
            mock.call.get_framework("g-cloud-99"),
            mock.call.find_framework_suppliers_iter("g-cloud-99"),
            mock.call.find_users_iter(supplier_id=303132),
            mock.call.find_users_iter(supplier_id=303233),
            mock.call.find_users_iter(supplier_id=303133),
            mock.call.find_users_iter(supplier_id=313233),
        ]
        assert self.mock_notify_client.mock_calls == [
            mock.call.get_reference("one@peasoup.net", "8877eeff", {
                'framework_slug': 'g-cloud-99',
                'run_id': expected_run_id,
            }),
            (mock.call.has_been_sent(
                f"one@peasoup.net,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}"
            ) if dry_run else mock.call.send_email(
                'one@peasoup.net',
                '8877eeff',
                self.expected_context,
                allow_resend=False,
                reference=f"one@peasoup.net,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}",
            )),
            mock.call.get_reference("two@peasoup.net", "8877eeff", {
                'framework_slug': 'g-cloud-99',
                'run_id': expected_run_id,
            }),
            (mock.call.has_been_sent(
                f"two@peasoup.net,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}",
            ) if dry_run else mock.call.send_email(
                'two@peasoup.net',
                '8877eeff',
                self.expected_context,
                allow_resend=False,
                reference=f"two@peasoup.net,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}",
            )),
            mock.call.get_reference("two@shirts.co.ua", "8877eeff", {
                'framework_slug': 'g-cloud-99',
                'run_id': expected_run_id,
            }),
            (mock.call.has_been_sent(
                f"two@shirts.co.ua,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}",
            ) if dry_run else mock.call.send_email(
                'two@shirts.co.ua',
                '8877eeff',
                self.expected_context,
                allow_resend=False,
                reference=f"two@shirts.co.ua,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}",
            )),
            mock.call.get_reference("three@shirts.co.ua", "8877eeff", {
                'framework_slug': 'g-cloud-99',
                'run_id': expected_run_id,
            }),
            (mock.call.has_been_sent(
                f"three@shirts.co.ua,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}",
            ) if dry_run else mock.call.send_email(
                'three@shirts.co.ua',
                '8877eeff',
                self.expected_context,
                allow_resend=False,
                reference=f"three@shirts.co.ua,8877eeff,{{'framework_slug': 'g-cloud-99', 'run_id': '{expected_run_id}'}}",
            )),
        ]

        assert dry_run == (
            mock.call.debug(
                "[DRY RUN] Would NOT send notification to {email_hash} (already sent)",
                extra=mock.ANY,
            ) in self.mock_logger.mock_calls
        )

    def test_sending_failure_continues(self):

        def _send_email_side_effect(email_address, *args, **kwargs):
            if email_address == "two@peasoup.net":
                raise EmailError("foo")
            return {}

        self.mock_notify_client.send_email.side_effect = _send_email_side_effect

        assert notify_suppliers_of_framework_application_event(
            data_api_client=self.mock_data_api_client,
            notify_client=self.mock_notify_client,
            notify_template_id="8877eeff",
            framework_slug="g-cloud-99",
            dry_run=False,
            stage="production",
            logger=self.mock_logger,
            run_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        ) == 1

        assert mock.call.error(
            "Failed sending to {email_hash}: {e}",
            extra={
                "email_hash": mock.ANY,
                "e": AnyStringMatching("foo"),
            },
        ) in self.mock_logger.mock_calls

        # check that we do actually end up trying to send all emails instead of giving up after error
        assert tuple(call[0][0] for call in self.mock_notify_client.send_email.call_args_list) == (
            "one@peasoup.net",
            "two@peasoup.net",
            "two@shirts.co.ua",
            "three@shirts.co.ua",
        )
