import builtins
import mock
import pytest
from dmapiclient.errors import HTTPError

from dmscripts.suspend_suppliers_without_agreements import (
    suspend_supplier_services, get_all_email_addresses_for_supplier
)


class TestSuspendSupplierServices:

    def setup(self):
        self.data_api_client = mock.Mock()
        self.data_api_client.find_services.return_value = {
            'services': [
                {'id': 1},
                {'id': 2}
            ],
            "meta": {
                "total": 2
            }
        }
        self.logger = mock.Mock()

    def test_suspend_supplier_services_updates_services_and_returns_count(self):
        framework_interest = {
            "frameworkInterest": {
                "onFramework": True,
                "agreementReturned": False,
                "agreementStatus": None
            }
        }

        assert suspend_supplier_services(
            self.data_api_client, self.logger, 'g-cloud-11', 12345, framework_interest) == 2

        assert self.data_api_client.find_services.call_args_list == [
            mock.call(supplier_id=12345, framework='g-cloud-11', status='published')
        ]
        assert self.data_api_client.update_service_status.call_args_list == [
            mock.call(1, 'disabled', "Suspend services script"),
            mock.call(2, 'disabled', "Suspend services script"),
        ]
        assert self.logger.info.call_args_list == [
            mock.call("Setting 2 services to 'disabled' for supplier 12345.")
        ]

    def test_suspend_supplier_services_skips_if_no_services(self):
        framework_interest = {
            "frameworkInterest": {
                "onFramework": True,
                "agreementReturned": False,
                "agreementStatus": None
            }
        }
        self.data_api_client.find_services.return_value = {'services': []}

        assert suspend_supplier_services(
            self.data_api_client, self.logger, 'g-cloud-11', 12345, framework_interest) == 0

        assert self.data_api_client.find_services.call_args_list == [
            mock.call(supplier_id=12345, framework='g-cloud-11', status='published')
        ]
        assert self.data_api_client.update_service_status.call_args_list == []
        assert self.logger.error.call_args_list == [
            mock.call("Supplier 12345 has no published services on the framework.")
        ]

    def test_suspend_supplier_services_skips_if_not_on_framework(self):
        framework_interest = {
            "frameworkInterest": {
                "onFramework": False,
                "agreementReturned": False,
                "agreementStatus": None
            }
        }

        assert suspend_supplier_services(
            self.data_api_client, self.logger, 'g-cloud-11', 12345, framework_interest) == 0

        assert self.data_api_client.find_services.call_args_list == []
        assert self.data_api_client.update_service_status.call_args_list == []
        assert self.logger.error.call_args_list == [
            mock.call("Supplier 12345 is not on the framework.")
        ]

    def test_suspend_supplier_services_skips_if_agreement_returned(self):
        framework_interest = {
            "frameworkInterest": {
                "onFramework": True,
                "agreementReturned": True,
                "agreementStatus": None
            }
        }

        assert suspend_supplier_services(
            self.data_api_client, self.logger, 'g-cloud-11', 12345, framework_interest) == 0

        assert self.data_api_client.find_services.call_args_list == []
        assert self.data_api_client.update_service_status.call_args_list == []
        assert self.logger.error.call_args_list == [
            mock.call("Supplier 12345 has returned their framework agreement.")
        ]

    def test_suspend_supplier_services_skips_if_agreement_on_hold(self):
        framework_interest = {
            "frameworkInterest": {
                "onFramework": True,
                "agreementReturned": False,
                "agreementStatus": "on-hold"
            }
        }

        assert suspend_supplier_services(
            self.data_api_client, self.logger, 'g-cloud-11', 12345, framework_interest) == 0

        assert self.data_api_client.find_services.call_args_list == []
        assert self.data_api_client.update_service_status.call_args_list == []
        assert self.logger.error.call_args_list == [
            mock.call("Supplier 12345's framework agreement is on hold.")
        ]


class TestGetAllEmailAddressesForSupplier:

    def test_get_all_email_addresses_for_supplier(self):
        data_api_client = mock.Mock()
        data_api_client.find_users_iter.return_value = [
            {"emailAddress": "one_inch_nail@example.com", "active": True},
            {"emailAddress": "two_inch_nails@example.com", "active": True},
            {"emailAddress": "three_inch_nails@example.com", "active": False},
        ]
        framework_interest = {
            "frameworkInterest": {
                "supplierId": 12345,
                "declaration": {
                    "primaryContactEmail": "trent.reznor@example.com"
                }
            }
        }

        assert get_all_email_addresses_for_supplier(data_api_client, framework_interest) == {
            "trent.reznor@example.com",
            "one_inch_nail@example.com",
            "two_inch_nails@example.com"
        }
        assert data_api_client.find_users_iter.call_args_list == [
            mock.call(supplier_id=12345)
        ]
