import pytest
import requests

from dmscripts.helpers.supplier_data_helpers import country_code_to_name


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
