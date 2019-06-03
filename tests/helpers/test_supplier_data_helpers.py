import pytest
import requests

from docopt import docopt

from dmscripts.helpers.supplier_data_helpers import (
    country_code_to_name,
    get_supplier_ids_from_args,
    AppliedToFrameworkSupplierContextForNotify,
    SupplierFrameworkData,
)
from dmscripts.data_retention_remove_supplier_declarations import SupplierFrameworkDeclarations
from tests.assessment_helpers import BaseAssessmentTest
import mock
import json
from freezegun import freeze_time


class TestSupplierFrameworkDeclarations(BaseAssessmentTest):

    @pytest.fixture
    def mocked_api_client(self):
        from dmapiclient import DataAPIClient
        mocked_api_client = mock.create_autospec(DataAPIClient)
        with freeze_time("Jan 1st, 2018"):
            mocked_api_client.find_frameworks.return_value = {
                "frameworks": [
                    {
                        "slug": "framework-expired-yesterday",
                        "frameworkExpiresAtUTC": "2017-12-31T23:59:59.999999Z"
                    },
                    {
                        "slug": "framework-expired-almost-three-years-ago",
                        "frameworkExpiresAtUTC": "2015-01-03T23:59:59.999999Z"
                    },
                    {
                        "slug": "framework-expired-three-years-ago",
                        "frameworkExpiresAtUTC": "2015-01-02T00:00:00.000000Z"
                    },
                    {
                        "slug": "framework-expired-a-decade-ago",
                        "frameworkExpiresAtUTC": "2008-01-04T23:59:59.999999Z"
                    }
                ]
            }
            mocked_api_client.find_framework_suppliers_iter.side_effect = lambda *args, **kwargs: \
                iter(self._supplier_framework_response())
        return mocked_api_client

    def _supplier_framework_response(self):
        with open("tests/fixtures/test_supplier_frameworks_response.json", 'r') as response_file:
            return json.load(response_file)['supplierFrameworks']

    def test_suppliers_application_failed_to_framework(self, mocked_api_client):
        supplier_framework = SupplierFrameworkDeclarations(
            mocked_api_client,
            mock.MagicMock(),
            dry_run=False,
            user='Data Retention Script'
        )
        assert supplier_framework.suppliers_application_failed_to_framework('g-cloud-8') == [12345, 23456]

    def test_remove_declaration_from_suppliers(self, mocked_api_client):
        with freeze_time('2019-01-01 12:00:00'):
            mocked_api_client.remove_supplier_declaration.return_value = {'declaration': {}}
            sfd = SupplierFrameworkDeclarations(
                mocked_api_client,
                mock.MagicMock(),
                dry_run=False,
                user='Data Retention Script'
            )
            assert sfd.remove_declaration(1, 'g-cloud-8')['declaration'] == {}
            mocked_api_client.remove_supplier_declaration.assert_called_with(
                1,
                'g-cloud-8',
                'Data Retention Script 2019-01-01T12:00:00')

    def test_remove_supplier_declaration_for_expired_frameworks(self, mocked_api_client):
        with freeze_time("Jan 1st, 2018"):
            sfd = SupplierFrameworkDeclarations(
                mocked_api_client,
                mock.MagicMock(),
                dry_run=False,
                user='Data Retention Script'
            )
            sfd.remove_supplier_declaration_for_expired_frameworks()
            expected_calls = [
                mock.call(framework_slug="framework-expired-three-years-ago", with_declarations=None),
                mock.call(framework_slug="framework-expired-a-decade-ago", with_declarations=None)
            ]
            mocked_api_client.find_framework_suppliers_iter.assert_has_calls(expected_calls, any_order=True)

    def test_remove_declaration_from_failed_applicants(self, mocked_api_client):
        with freeze_time("2019-01-01 12:00:00"):
            sfd = SupplierFrameworkDeclarations(
                mocked_api_client,
                mock.MagicMock(),
                dry_run=False,
                user='Data Retention Script'
            )
            sfd.remove_declaration_from_failed_applicants(framework_slug='g-cloud-8')
            expected_calls = [
                mock.call(
                    supplier_id=12345,
                    framework_slug='g-cloud-8',
                    user='Data Retention Script 2019-01-01T12:00:00'),
                mock.call(
                    supplier_id=23456,
                    framework_slug='g-cloud-8',
                    user='Data Retention Script 2019-01-01T12:00:00')
            ]
            mocked_api_client.remove_supplier_declaration.assert_has_calls(expected_calls, any_order=True)


class TestSupplierFrameworkData:
    def test_get_supplier_frameworks_returns_framework_suppliers(self, mock_data_client):
        data = SupplierFrameworkData(mock_data_client, "g-cloud-11")

        mock_data_client.find_framework_suppliers_iter.return_value = [mock.sentinel.framework_suppliers]
        assert data.get_supplier_frameworks() == [mock.sentinel.framework_suppliers]

    def test_get_supplier_frameworks_can_filter_by_supplier_ids(self, mock_data_client):
        data = SupplierFrameworkData(mock_data_client, "g-cloud-11", supplier_ids=[2])

        mock_data_client.find_framework_suppliers_iter.return_value = [
            {"supplierId": 1},
            {"supplierId": 2},
        ]
        assert data.get_supplier_frameworks() == [{"supplierId": 2}]

    def test_get_supplier_users_returns_dict_of_users_grouped_by_supplier(self, mock_data_client):
        data = SupplierFrameworkData(mock_data_client, "g-cloud-11")

        mock_data_client.export_users.return_value = {"users": [
            {"id": 1, "supplier_id": 1},
            {"id": 2, "supplier_id": 2},
            {"id": 3, "supplier_id": 1},
        ]}
        assert data.get_supplier_users() == {
            1: [{"id": 1, "supplier_id": 1}, {"id": 3, "supplier_id": 1}],
            2: [{"id": 2, "supplier_id": 2}],
        }

    def test_get_supplier_users_can_filter_by_supplier_id(self, mock_data_client):
        data = SupplierFrameworkData(mock_data_client, "g-cloud-11", supplier_ids=[2])

        mock_data_client.export_users.return_value = {"users": [
            {"id": 1, "supplier_id": 1},
            {"id": 2, "supplier_id": 2},
            {"id": 3, "supplier_id": 1},
        ]}
        assert data.get_supplier_users() == {
            2: [{"id": 2, "supplier_id": 2}],
        }

    def test_populate_data_can_filter_by_supplier_ids(self, mock_data_client):
        data = SupplierFrameworkData(mock_data_client, "g-cloud-11", supplier_ids=[2])

        mock_data_client.find_framework_suppliers_iter.return_value = [
            {"supplierId": 1},
            {"supplierId": 2},
        ]
        mock_data_client.export_users.return_value = {"users": [
            {"id": 1, "supplier_id": 1},
            {"id": 2, "supplier_id": 2},
            {"id": 3, "supplier_id": 1},
        ]}

        data.populate_data()

        assert data.data == [{"supplierId": 2, "users": [{"id": 2, "supplier_id": 2}], "draft_services": []}]
        assert mock_data_client.find_draft_services_iter.call_args_list == [mock.call(2, framework="g-cloud-11")]


class TestAppliedToFrameworkSupplierContextForNotify:
    def test_get_suppliers_with_users_personalisations_groups_users_by_supplier_id(
        self, mock_data_client
    ):
        data = AppliedToFrameworkSupplierContextForNotify(
            mock_data_client,
            "g-cloud-11",
            supplier_ids=[12345],
        )
        data.populate_data()

        results = {supplier: list(users) for supplier, users in data.get_suppliers_with_users_personalisations()}

        assert list(results.keys()) == [12345]
        assert len(results[12345]) == 1
        assert "email address" in results[12345][0][0]
        assert "applied" in results[12345][0][1]

    def test_template_personalisation_whether_supplier_has_applied_to_framework(
        self, mock_data_client
    ):
        data = AppliedToFrameworkSupplierContextForNotify(
            mock_data_client, "g-cloud-11",
        )
        data.populate_data()

        assert all("applied" in p for p in data.get_users_personalisations().values())


class TestCountryCodeToName:
    GB_COUNTRY_JSON = {
        "GB": {
            "index-entry-number": "6",
            "entry-number": "6",
            "entry-timestamp": "2016-04-05T13:23:05Z",
            "key": "GB",
            "item": [{
                "country": "GB",
                "official-name": "The United Kingdom of Great Britain and Northern Ireland",
                "name": "United Kingdom",
                "citizen-names": "Briton;British citizen"
            }]
        }
    }

    GG_TERRITORY_JSON = {
        "GG": {
            "index-entry-number": "35",
            "entry-number": "35",
            "entry-timestamp": "2016-12-15T12:15:07Z",
            "key": "GG",
            "item": [{
                "official-name": "Bailiwick of Guernsey",
                "name": "Guernsey",
                "territory": "GG"
            }]
        }
    }

    def setup(self):
        country_code_to_name.cache_clear()

    @pytest.mark.parametrize('full_code, expected_url, response, expected_name',
                             (
                                 ('country:GB', 'https://country.register.gov.uk/records/GB.json',
                                  GB_COUNTRY_JSON, 'United Kingdom'),
                                 ('territory:GG', 'https://territory.register.gov.uk/records/GG.json',
                                  GG_TERRITORY_JSON, 'Guernsey'),
                             ))
    def test_correct_url_requested_and_code_converted_to_name(self, rmock, full_code, expected_url, response,
                                                              expected_name):
        rmock.get(
            expected_url,
            json=response,
            status_code=200
        )

        country_name = country_code_to_name(full_code)

        assert country_name == expected_name

    def test_404_raises(self, rmock):
        rmock.get(
            'https://country.register.gov.uk/records/GB.json',
            status_code=404,
        )

        with pytest.raises(requests.exceptions.RequestException):
            country_code_to_name('country:GB')

    def test_responses_are_cached(self, rmock):
        rmock.get(
            'https://country.register.gov.uk/records/GB.json',
            json=self.GB_COUNTRY_JSON,
            status_code=200
        )

        country_code_to_name('country:GB')
        country_code_to_name('country:GB')

        assert len(rmock.request_history) == 1
        assert country_code_to_name.cache_info().hits == 1
        assert country_code_to_name.cache_info().misses == 1
        assert country_code_to_name.cache_info().maxsize == 128

    def test_retries_if_not_200(self, rmock):
        rmock.get(
            'https://country.register.gov.uk/records/GB.json',
            [{'json': {}, 'status_code': 500},
             {'json': self.GB_COUNTRY_JSON, 'status_code': 200}],
        )

        country_name = country_code_to_name('country:GB')

        assert country_name == 'United Kingdom'
        assert len(rmock.request_history) == 2


class TestSupplierIDsHelpers:

    @pytest.fixture
    def parse_docopt(self):
        return lambda argv: docopt("Usage: test [ --supplier-id=<id> ... | --supplier-ids-from=<file> ]", argv)

    def test_get_supplier_ids_from_args_parses_output_of_docopt(self, parse_docopt):
        args = parse_docopt("--supplier-id=1 --supplier-id=2")
        get_supplier_ids_from_args(args) == [1, 2]

        with mock.patch("dmscripts.helpers.supplier_data_helpers.get_supplier_ids_from_file") as m:
            args = parse_docopt(f"--supplier-ids-from={mock.sentinel.supplier_ids_file}")
            get_supplier_ids_from_args(args)
            assert m.called_with(mock.sentinel.supplier_ids_file)

    def test_get_supplier_ids_can_handle_comma_separated_supplier_ids(self, parse_docopt):
        args = parse_docopt("--supplier-id=1,2,3")
        get_supplier_ids_from_args(args) == [1, 2, 3]

        args = parse_docopt("--supplier-id=1,2,3 --supplier-id=4")
        get_supplier_ids_from_args(args) == [1, 2, 3, 4]
