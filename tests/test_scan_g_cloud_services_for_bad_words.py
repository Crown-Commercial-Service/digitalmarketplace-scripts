import mock
import pytest

from dmapiclient import DataAPIClient
from dmscripts.scan_g_cloud_services_for_bad_words import scan_services_for_bad_words


class TestScanServicesForBadWords:

    def setup(self):
        self.client = mock.Mock(autospec=DataAPIClient)
        self.client.find_framework_suppliers.return_value = {
            "supplierFrameworks": [
                {'supplierId': 1, 'onFramework': True}, {'supplierId': 2, 'onFramework': False}
            ]
        }
        self.client.find_draft_services_by_framework_iter.return_value = [
            {"serviceDescription": "Whoops I left some Lorem ipsum in here"}
        ]

        self.logger = mock.Mock()
        self.content_loader = mock.Mock()
        self.content_loader.get_metadata.return_value = ['serviceDescription']

    @pytest.mark.parametrize('scan_drafts', (False, True))
    @mock.patch('dmscripts.scan_g_cloud_services_for_bad_words._get_bad_words_from_file')
    @mock.patch('dmscripts.scan_g_cloud_services_for_bad_words.check_services_with_bad_words')
    def test_scan_services_for_bad_words(self, check_services_with_bad_words, _get_bad_words_from_file, scan_drafts):
        _get_bad_words_from_file.return_value = ['lorem', 'ipsum']
        scan_services_for_bad_words(
            self.client,
            "path/to/bad-words-file.txt",
            "g-cloud-12",
            "output-dir",
            self.content_loader,
            self.logger,
            scan_drafts
        )

        assert self.client.find_framework_suppliers.call_args_list == [
            mock.call('g-cloud-12', with_declarations=None)
        ]
        assert self.content_loader.get_metadata.call_args_list == [
            mock.call('g-cloud-12', 'service_questions_to_scan_for_bad_words', 'service_questions')
        ]
        assert check_services_with_bad_words.call_args_list == [
            mock.call(
                'output-dir/g-cloud-12-services-with-blacklisted-words.csv',
                "g-cloud-12",
                self.client,
                [{'supplierId': 1, 'onFramework': True}],
                ['lorem', 'ipsum'],
                ['serviceDescription'],
                self.logger,
                scan_drafts,
            )
        ]
