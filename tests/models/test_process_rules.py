import pytest
import mock

import pandas
from dmscripts.models.process_rules import (
    format_datetime_string_as_date,
    remove_username_from_email_address,
    extract_id_from_user_info,
    query_data_from_config
)
from dmapiclient import DataAPIClient


def test_format_datetime_string_as_date():
    initial_date = "2016-10-08T12:00:00.00000Z"
    formatted_date = "2016-10-08"
    assert format_datetime_string_as_date(initial_date) == formatted_date


def test_format_datetime_string_as_date_raises_error_if_initial_date_format_incorrect():
    initial_dates = (
        "2016-10-08T12:00:00.00000",
        "2016-10-08T12:00:00",
        "2016-10-08"
    )
    for date in initial_dates:
        with pytest.raises(ValueError) as excinfo:
            format_datetime_string_as_date(date)

        assert "time data '{}' does not match format".format(date) in str(excinfo.value)


def test_remove_username_from_email_address():
    initial_email_address = "user.name@domain.com"
    formatted_email_address = "domain.com"
    assert remove_username_from_email_address(initial_email_address) == formatted_email_address


def test_extract_id_from_user_info():
    user_list = [{'id': x} for x in range(3)]
    extracted_ids = extract_id_from_user_info(user_list)

    assert extracted_ids == '0,1,2'


class TestQueryDataFromConfig:

    @mock.patch('dmscripts.models.queries.base_model')
    def test_query_data_from_config_queries_db_given_a_base_model(self, base_model):
        config = {
            'name': 'completed_outcomes',
            'base_model': 'outcomes',
            'get_data_kwargs': {'completed': True},
            'keys': (
                'id',
                'result',
                ('resultOfDirectAward', 'project', 'id',),
            )
        }
        client = mock.Mock(autospec=DataAPIClient)
        expected_query_result = pandas.DataFrame([{'id': '1', 'result': 'awarded'}])
        base_model.side_effect = [expected_query_result]

        assert query_data_from_config(
            config, logger=mock.ANY, limit=100, client=client, output_dir="data"
        ).equals(expected_query_result)

        # What this test is really concerned with - we call queries.base_model rather than queries.model
        assert base_model.call_args_list == [
            mock.call(
                'outcomes',
                ['id', 'result', ('resultOfDirectAward', 'project', 'id')],
                {'completed': True},
                client=client,
                limit=100,
                logger=mock.ANY
            )
        ]

    @mock.patch('dmscripts.models.queries.model')
    def test_query_data_from_config_reads_file_given_a_non_base_model(self, model):
        config = {
            'name': 'successful_brief_responses',
            'model': 'brief_responses',
            'keys': (
                'briefId',
                'lot',
                'title',
            )
        }
        client = mock.Mock(autospec=DataAPIClient)
        expected_query_result = pandas.DataFrame([{'briefId': '1', 'lot': 'digital-outcomes', 'title': 'ABC'}])
        model.side_effect = [expected_query_result]

        result = query_data_from_config(
            config, logger=mock.ANY, limit=100, client=client, output_dir="data"
        )

        assert list(result.columns) == ['briefId', 'lot', 'title']
        assert result.values.tolist()[0] == ['1', 'digital-outcomes', 'ABC']

        # What this test is really concerned with - we call queries.model rather than queries.base_model
        assert model.call_args_list == [
            mock.call('brief_responses', directory='data')
        ]

    @mock.patch('dmscripts.models.queries.join')
    @mock.patch('dmscripts.models.queries.model')
    def test_query_data_from_config_applies_joins(self, model, join):
        config = {
            'name': 'successful_brief_responses',
            'model': 'brief_responses',
            'keys': ('briefId',),
            'joins': [
                {
                    'model_name': 'briefs',
                    'left_on': 'briefId',
                    'right_on': 'id',
                    'data_duplicate_suffix': '_brief_responses'
                }
            ]
        }
        client = mock.Mock(autospec=DataAPIClient)

        expected_query_result = pandas.DataFrame([{'briefId': '1', 'lot': 'digital-outcomes', 'title': 'ABC'}])
        model.side_effect = [expected_query_result]

        query_data_from_config(config, logger=mock.ANY, limit=100, client=client, output_dir="data")

        # Check that the join is called with the correct args
        assert join.call_args_list == [
            mock.call(
                expected_query_result,
                data_duplicate_suffix='_brief_responses',
                directory='data',
                left_on='briefId',
                model_name='briefs',
                right_on='id'
            )
        ]
        # TODO: A more thorough test would check the two data frames were joined correctly instead of patching
        # queries.join, but we have coverage in tests/models/test_queries.py for this

    @mock.patch('dmscripts.models.queries.model')
    def test_query_data_from_config_assign_json_subfields(self, model):
        config = {
            'name': 'successful_brief_responses',
            'model': 'brief_responses',
            'keys': ('briefId', 'awardedContractStartDate', 'awardedContractValue',),
            'assign_json_subfields': {
                'awardDetails': ['awardedContractStartDate', 'awardedContractValue'],
            }
        }
        client = mock.Mock(autospec=DataAPIClient)

        expected_query_result = pandas.DataFrame([{
            'briefId': '1',
            'awardDetails': {'awardedContractStartDate': '2019-01-01', 'awardedContractValue': '10000'}
        }])
        model.side_effect = [expected_query_result]

        result = query_data_from_config(
            config, logger=mock.ANY, limit=100, client=client, output_dir="data"
        )
        assert list(result.columns) == ['briefId', 'awardedContractStartDate', 'awardedContractValue']
        assert result.values.tolist()[0] == ['1', '2019-01-01', '10000']

    @mock.patch('dmscripts.models.queries.model')
    def test_query_data_from_config_renames_fields(self, model):
        config = {
            'name': 'successful_brief_responses',
            'model': 'brief_responses',
            'keys': ('briefId', 'status_briefs',),
            'rename_fields': {'status_briefs': 'status'}
        }
        client = mock.Mock(autospec=DataAPIClient)

        expected_query_result = pandas.DataFrame([{'briefId': '1', 'status_briefs': 'closed'}])
        model.side_effect = [expected_query_result]

        result = query_data_from_config(
            config, logger=mock.ANY, limit=100, client=client, output_dir="data"
        )
        assert list(result.columns) == ['briefId', 'status']
        assert result.values.tolist()[0] == ['1', 'closed']
