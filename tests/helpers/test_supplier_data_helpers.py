import pytest
import requests

from dmscripts.helpers.supplier_data_helpers import country_code_to_name
from dmscripts.data_retention_remove_supplier_declarations import SupplierFrameworkDeclarations
from tests.assessment_helpers import BaseAssessmentTest
import mock
from dmapiclient import DataAPIClient
import json


class TestSupplierFrameworkDeclarations(BaseAssessmentTest):

    def _supplier_framework_response(self):
        with open("tests/fixtures/test_supplier_frameworks_response.json", 'r') as response_file:
            return json.load(response_file)['supplierFrameworks']

    def test_suppliers_application_failed_to_framework(self):
        mocked_api_client = mock.create_autospec(DataAPIClient)
        mocked_api_client.find_framework_suppliers_iter.side_effect = lambda *args, **kwargs: \
            iter(self._supplier_framework_response())
        supplier_framework = SupplierFrameworkDeclarations(mocked_api_client, mock.ANY, 'g-cloud-8', dry_run=False)
        assert supplier_framework.suppliers_application_failed_to_framework() == [12345, 23456]

    def test_remove_declaration_from_suppliers(self):
        mocked_api_client = mock.create_autospec(DataAPIClient)
        mocked_api_client.remove_supplier_declaration.return_value = {'declaration': {}}
        sfd = SupplierFrameworkDeclarations(mocked_api_client, mock.ANY, 'g-cloud-8', dry_run=False)
        assert sfd.remove_declaration(1, 'g-cloud-8')['declaration'] == {}
        mocked_api_client.remove_supplier_declaration.assert_called_with(1, 'g-cloud-8', 'user')


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
