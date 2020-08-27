import mock
import pytest
from dmapiclient import DataAPIClient
from dmcontent.content_loader import ContentLoader
from scripts.oneoff.update_draft_service_via_csv import (
    find_draft_id_by_service_name,
    get_price_data,
    lookup_question_id_and_text,
    parse_answer_from_csv_row,
    update_draft_services_from_folder
)


class TestFindDraftIDByServiceName:

    def test_find_draft_id_by_service_name_finds_draft_id(self):
        client = mock.Mock(autospec=DataAPIClient)
        client.find_draft_services_by_framework_iter.return_value = [
            {'id': 998, 'serviceName': 'My Other Service Name'},
            {'id': 999, 'serviceName': 'My Service Name'},
        ]

        assert find_draft_id_by_service_name(client, "12345", "myservicename", "g-cloud-12") == 999

    def test_find_draft_id_by_service_name_raises_if_no_matching_service_name(self):
        client = mock.Mock(autospec=DataAPIClient)
        client.find_draft_services_by_framework_iter.return_value = [
            {'id': 998, 'serviceName': 'My Other Service Name'},
            {'id': 999, 'serviceName': 'My Rubbish Service Name'},
        ]
        assert find_draft_id_by_service_name(client, "12345", "myservicename", "g-cloud-12") is None

    def test_find_draft_id_by_service_name_raises_if_multiple_matching_service_names(self):
        client = mock.Mock(autospec=DataAPIClient)
        client.find_draft_services_by_framework_iter.return_value = [
            {'id': 998, 'serviceName': 'My Service Name'},
            {'id': 999, 'serviceName': 'My Service Name'},
        ]
        assert find_draft_id_by_service_name(client, "12345", "myservicename", "g-cloud-12") == 'multi'


class TestGetPriceData:

    @pytest.mark.parametrize(
        'answers, expected',
        [
            (
                ["1", "3", 'per user', 'per day'],
                {'priceMin': "1", 'priceMax': "3", 'priceUnit': 'User', 'priceInterval': 'Day'}
            ),
            (
                ["1", 'per user'],
                {'priceMin': "1", 'priceUnit': 'User'}
            ),
            (
                ["1", 'per user', 'per day'],
                {'priceMin': "1", 'priceUnit': 'User', 'priceInterval': 'Day'}
            ),
            (
                ["1", "3", 'per user'],
                {'priceMin': "1", 'priceMax': "3", 'priceUnit': 'User'}
            ),
            (
                ["£1", "£3", 'per user'],
                {'priceMin': "1", 'priceMax': "3", 'priceUnit': 'User'}
            ),
        ]
    )
    def test_get_price_data(self, answers, expected):
        assert get_price_data(answers) == expected


class TestLookupQuestionTextAndID:

    def test_lookup_question_id_and_text(self):
        row = {
            'Question': 'Very Important Question'
        }
        questions = {
            'Very Important Question': mock.Mock(id='veryImportantQuestion')
        }
        assert lookup_question_id_and_text(row, questions) == ('veryImportantQuestion', 'Very Important Question')

    def test_lookup_question_id_and_text_handles_curly_apostrophes(self):
        row = {
            'Question': "It's A Very Important Question"
        }
        questions = {
            "It’s A Very Important Question": mock.Mock(id='veryImportantQuestion')
        }
        assert lookup_question_id_and_text(row, questions) == (
            'veryImportantQuestion', "It’s A Very Important Question"
        )

    def test_lookup_question_id_and_text_returns_null_if_not_found(self):
        row = {
            'Question': "Very Important Question"
        }
        questions = {
            "A Different Question": mock.Mock(id='veryImportantQuestion')
        }
        assert lookup_question_id_and_text(row, questions) == (None, None)


class TestParseAnswerFromCSVRow:

    cloud_support_row = {
        'Question': 'Very Important Question',
        'Answer 1': '',
        'Answer 2': '',
        'Answer 3': '',
        'Answer 4': '',
        'Answer 5': '',
        'Answer 6': '',
        'Answer 7': '',
        'Answer 8': '',
        'Answer 9': '',
        'Answer 10': '',
    }

    questions = {
        'Which categories does your service fit under?': mock.Mock(),
        'Pick a card any card': mock.Mock(
            options=(
                {'label': 'Option 1', 'value': 'option_1'},
                {'label': 'Option 2', 'value': 'option_2'},
            )
        ),
        'Tick at least two things': mock.Mock(type='checkboxes', options=None),
        'List at least two things': mock.Mock(type='list', options=None),
        'Enter your name': mock.Mock(options=None),
        'How much does the service cost (excluding VAT)?': mock.Mock(options=None),
    }

    def _mock_question(self, type=None, options=None):
        mock_question = mock.Mock()
        mock_question.type = type if type else 'text'
        mock_question.options = options if options else []

    def test_parse_answer_from_csv_row_returns_none_for_blank_answer(self):
        assert parse_answer_from_csv_row(
            self.cloud_support_row, self.questions, 'Very Important Question', 'cloud-support'
        ) is None

    def test_parse_answer_from_csv_row_service_categories(self):
        row = self.cloud_support_row.copy()
        question_text = 'Which categories does your service fit under?'
        row['Question'] = question_text
        row['Answer 1'] = 'Bathtime'
        row['Answer 2'] = 'Benidorm'
        # Answer 3 column left blank
        row['Answer 4'] = 'Bananas'

        assert parse_answer_from_csv_row(row, self.questions, question_text, 'cloud-support') == [
            'Bathtime', 'Benidorm', 'Bananas'
        ]

    def test_parse_answer_from_csv_option_labels(self):
        row = self.cloud_support_row.copy()
        question_text = 'Pick a card any card'
        row['Question'] = question_text
        row['Answer 1'] = 'Option 1'
        row['Answer 2'] = 'Option 2'

        assert parse_answer_from_csv_row(row, self.questions, question_text, 'cloud-support') == [
            'option_1', 'option_2'
        ]

    def test_parse_answer_from_csv_list_question(self):
        row = self.cloud_support_row.copy()
        question_text = 'List at least two things'
        row['Question'] = question_text
        row['Answer 1'] = 'Thing 1'
        row['Answer 2'] = 'Thing 2'

        assert parse_answer_from_csv_row(row, self.questions, question_text, 'cloud-support') == [
            'Thing 1', 'Thing 2'
        ]

    def test_parse_answer_from_csv_checkbox_question(self):
        row = self.cloud_support_row.copy()
        question_text = 'Tick at least two things'
        row['Question'] = question_text
        row['Answer 1'] = 'Thing 1'
        row['Answer 2'] = 'Thing 2'

        assert parse_answer_from_csv_row(row, self.questions, question_text, 'cloud-support') == [
            'Thing 1', 'Thing 2'
        ]

    def test_parse_answer_from_csv_price_question(self):
        row = self.cloud_support_row.copy()
        question_text = 'How much does the service cost (excluding VAT)?'
        row['Question'] = question_text
        row['Answer 1'] = '£1'
        row['Answer 2'] = 'per hour'

        assert parse_answer_from_csv_row(row, self.questions, question_text, 'cloud-support') == {
            'priceInterval': 'Hour', 'priceMin': '1'
        }

    def test_parse_answer_from_csv_single_answer(self):
        row = self.cloud_support_row.copy()
        question_text = 'Enter your name'
        row['Answer 1'] = "Basil Brush"

        assert parse_answer_from_csv_row(row, self.questions, question_text, 'cloud-support') == 'Basil Brush'


@mock.patch('scripts.oneoff.update_draft_service_via_csv.create_draft_json_from_csv')
@mock.patch('scripts.oneoff.update_draft_service_via_csv.get_question_objects')
@mock.patch('scripts.oneoff.update_draft_service_via_csv.find_draft_id_by_service_name')
@mock.patch('scripts.oneoff.update_draft_service_via_csv.output_results')
@mock.patch('scripts.oneoff.update_draft_service_via_csv.get_all_files_of_type')
class TestUpdateDraftServicesFromFolder:

    def setup(self):
        self.content_loader = mock.Mock(autospec=ContentLoader)
        section = mock.Mock()
        section.get_field_names.return_value = ['bananas']
        self.content_loader.get_manifest.return_value.filter.return_value.sections = [section]

    @pytest.mark.parametrize('dry_run', (True, False))
    def test_update_draft_services_from_folder_successful(
        self, get_all_files_of_type, output_results, find_draft_id_by_service_name, get_question_objects,
        create_draft_json_from_csv, dry_run
    ):
        api_client = mock.Mock(autospec=DataAPIClient)
        api_client.get_draft_service.return_value = {"validationErrors": {}}

        get_all_files_of_type.return_value = [
            '/path/to/555777-cloud-software-myservice.csv',
        ]
        find_draft_id_by_service_name.return_value = 12345
        create_draft_json_from_csv.return_value = {}

        update_draft_services_from_folder(
            "~/local/folder", api_client, 'g-cloud-12', self.content_loader, dry_run, False
        )

        assert output_results.call_args_list == [
            # unidentifiable, malformed, successful, failed
            mock.call([], [], [('555777', '555777-cloud-software-myservice.csv', 12345)], [])
        ]
        assert self.content_loader.load_manifest.call_args_list == [
            mock.call('g-cloud-12', 'services', 'edit_submission')
        ]

    @pytest.mark.parametrize('dry_run', (True, False))
    def test_update_draft_services_from_folder_create_new_service(
        self, get_all_files_of_type, output_results, find_draft_id_by_service_name, get_question_objects,
        create_draft_json_from_csv, dry_run
    ):
        api_client = mock.Mock(autospec=DataAPIClient)
        api_client.create_new_draft_service.return_value = {"services": {"id": 999}}
        api_client.get_draft_service.return_value = {"validationErrors": {}}

        get_all_files_of_type.return_value = [
            '/path/to/555777-cloud-software-myservice.csv',
        ]
        create_draft_json_from_csv.return_value = {}

        update_draft_services_from_folder(
            "~/local/folder", api_client, 'g-cloud-12', self.content_loader, dry_run, True
        )

        assert output_results.call_args_list == [
            # unidentifiable, malformed, successful, failed
            mock.call([], [], [('555777', '555777-cloud-software-myservice.csv', 999)], [])
        ]
        assert self.content_loader.load_manifest.call_args_list == [
            mock.call('g-cloud-12', 'services', 'edit_submission')
        ]

    def test_update_draft_services_from_folder_failed(
        self, get_all_files_of_type, output_results, find_draft_id_by_service_name, get_question_objects,
        create_draft_json_from_csv
    ):
        api_client = mock.Mock(autospec=DataAPIClient)
        api_client.get_draft_service.return_value = {"validationErrors": {"not": "good"}}
        get_all_files_of_type.return_value = [
            '/path/to/555777-cloud-software-myservice.csv',
        ]
        find_draft_id_by_service_name.return_value = 12345
        create_draft_json_from_csv.return_value = {}

        update_draft_services_from_folder(
            "~/local/folder", api_client, 'g-cloud-12', self.content_loader, False, False
        )

        assert output_results.call_args_list == [
            # unidentifiable, malformed, successful, failed
            mock.call([], [], [], [('555777', '555777-cloud-software-myservice.csv', 12345, {'not': 'good'})])
        ]
        assert self.content_loader.load_manifest.call_args_list == [
            mock.call('g-cloud-12', 'services', 'edit_submission')
        ]

    @pytest.mark.parametrize('get_draft_response', (None, 'multi'))
    def test_update_draft_services_from_folder_unidentifiable(
        self, get_all_files_of_type, output_results, find_draft_id_by_service_name, get_question_objects,
        create_draft_json_from_csv, get_draft_response
    ):
        api_client = mock.Mock(autospec=DataAPIClient)
        content_loader = mock.Mock()
        get_all_files_of_type.return_value = [
            '/path/to/555777-cloud-software-myservice.csv',
        ]
        find_draft_id_by_service_name.return_value = get_draft_response

        update_draft_services_from_folder(
            "~/local/folder", api_client, 'g-cloud-12', content_loader, False, False
        )

        assert output_results.call_args_list == [
            # unidentifiable, malformed, successful, failed
            mock.call(['555777-cloud-software-myservice.csv'], [], [], [])
        ]

    def test_update_draft_services_from_folder_malformed_csv(
        self, get_all_files_of_type, output_results, find_draft_id_by_service_name, get_question_objects,
        create_draft_json_from_csv
    ):
        api_client = mock.Mock(autospec=DataAPIClient)
        api_client.get_draft_service.return_value = {"validationErrors": {}}
        content_loader = mock.Mock()
        get_all_files_of_type.return_value = [
            '/path/to/555777-cloud-software-myservice.csv',
        ]
        find_draft_id_by_service_name.return_value = 12345
        create_draft_json_from_csv.side_effect = UnicodeDecodeError("utf-8", b'bytesobject', 1, 2, "Yikes")

        update_draft_services_from_folder(
            "~/local/folder", api_client, 'g-cloud-12', content_loader, False, False
        )

        assert output_results.call_args_list == [
            # unidentifiable, malformed, successful, failed
            mock.call([], [('555777', '555777-cloud-software-myservice.csv')], [], [])
        ]
