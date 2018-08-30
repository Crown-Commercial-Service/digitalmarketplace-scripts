import mock
import pytest

from dmapiclient import HTTPError
from dmscripts.index_to_search_service import (
    do_index, BriefIndexer, ServiceIndexer

)


class TestIndexers:

    def setup(self):
        # Ensure we don't make any real API calls
        self.data_api_client_patch = mock.patch(
            'dmscripts.index_to_search_service.dmapiclient.DataAPIClient', autospec=True
        )
        self.data_api_client = self.data_api_client_patch.start()
        self.search_api_client_patch = mock.patch(
            'dmscripts.index_to_search_service.dmapiclient.SearchAPIClient', autospec=True
        )
        self.search_api_client = self.search_api_client_patch.start()

    def teardown(self):
        self.data_api_client_patch.stop()
        self.search_api_client_patch.stop()

    def test_brief_indexer_creates_index(self):
        indexer = BriefIndexer(
            'briefs', self.data_api_client.return_value, self.search_api_client.return_value, 'myIndex'
        )
        indexer.create_index('myMapping')

    def test_brief_indexer_skips_create_if_index_already_exists(self):
        self.search_api_client.return_value.create_index.side_effect = HTTPError(
            message='myIndex already exists as alias'
        )
        indexer = BriefIndexer(
            'briefs', self.data_api_client.return_value, self.search_api_client.return_value, 'myIndex'
        )
        indexer.create_index('myMapping')

    def test_brief_indexer_create_index_raises_on_other_api_errors(self):
        self.search_api_client.return_value.create_index.side_effect = HTTPError('disaster')
        indexer = BriefIndexer(
            'briefs', self.data_api_client.return_value, self.search_api_client.return_value, 'myIndex'
        )
        with pytest.raises(HTTPError) as e:
            indexer.create_index('myMapping')
            assert e.message == 'disaster'

    def test_brief_indexer_request_items_calls_data_api_client_with_frameworks(self):
        self.data_api_client.return_value.find_briefs_iter.return_value = ['brief1', 'brief2']
        indexer = BriefIndexer(
            'briefs', self.data_api_client.return_value, self.search_api_client.return_value, 'myIndex'
        )
        assert indexer.request_items('framework1,framework2') == ['brief1', 'brief2']
        assert self.data_api_client.return_value.find_briefs_iter.call_args_list == [
            mock.call(framework='framework1,framework2')
        ]

    def test_service_indexer_request_items_calls_data_api_client_with_frameworks(self):
        self.data_api_client.return_value.find_services_iter.return_value = ['service1', 'service2']
        indexer = ServiceIndexer(
            'services', self.data_api_client.return_value, self.search_api_client.return_value, 'myIndex'
        )
        assert indexer.request_items('framework1,framework2') == ['service1', 'service2']
        assert self.data_api_client.return_value.find_services_iter.call_args_list == [
            mock.call(framework='framework1,framework2')
        ]

    def test_brief_indexer_index_items_calls_search_api_client(self):
        self.data_api_client.return_value.find_briefs_iter.return_value = ['brief1', 'brief2']
        indexer = BriefIndexer(
            'briefs', self.data_api_client.return_value, self.search_api_client.return_value, 'myIndex'
        )
        indexer.index_item({'id': 'newBrief'})
        assert self.search_api_client.return_value.index.call_args_list == [
            mock.call('myIndex', 'newBrief', {'id': 'newBrief'}, 'briefs')
        ]

    def test_service_indexer_index_items_calls_search_api_index_for_published_services(self):
        self.data_api_client.return_value.find_services_iter.return_value = ['service1', 'service2']
        indexer = ServiceIndexer(
            'services', self.data_api_client.return_value, self.search_api_client.return_value, 'myIndex'
        )

        indexer.index_item({'id': 'newService', 'status': 'published'})
        assert self.search_api_client.return_value.index.call_args_list == [
            mock.call('myIndex', 'newService', {'id': 'newService', 'status': 'published'}, 'services')
        ]

    def test_service_indexer_index_items_calls_search_api_delete_for_published_services(self):
        self.data_api_client.return_value.find_services_iter.return_value = ['service1', 'service2']
        indexer = ServiceIndexer(
            'services', self.data_api_client.return_value, self.search_api_client.return_value, 'myIndex'
        )

        indexer.index_item({'id': 'newService', 'status': 'removed'})
        assert self.search_api_client.return_value.delete.call_args_list == [
            mock.call('myIndex', 'newService')
        ]

    @mock.patch.object(BriefIndexer, '__init__', autospec=True)
    @mock.patch.object(BriefIndexer, 'index_item', autospec=True)
    @mock.patch.object(BriefIndexer, 'request_items', autospec=True)
    def test_do_index_creates_brief_indexer_class_and_indexes_items(self, request_items, index_item, indexer_init):
        indexer_init.return_value = None
        request_items.return_value = ['brief1', 'brief2']
        do_index(
            'briefs',
            "http://search-api-url", "mySearchAPIToken",
            "http://data-api-url", "myDataAPIToken",
            mapping=False,
            serial=True,  # don't run in parallel for testing
            index="myIndex",
            frameworks="framework1,framework2"
        )

        assert indexer_init.call_args_list == [
            mock.call(
                mock.ANY, 'briefs', self.data_api_client.return_value, self.search_api_client.return_value, 'myIndex'
            )
        ]
        # Both API clients initialised when the BriefIndexer instance is created
        assert self.data_api_client.call_args_list == [mock.call('http://data-api-url', 'myDataAPIToken')]
        assert self.search_api_client.call_args_list == [mock.call('http://search-api-url', 'mySearchAPIToken')]

        assert request_items.call_args_list == [
            mock.call(mock.ANY, "framework1,framework2")
        ]
        assert index_item.call_args_list == [
            mock.call(mock.ANY, 'brief1'),
            mock.call(mock.ANY, 'brief2'),
        ]

    @mock.patch.object(ServiceIndexer, '__init__', autospec=True)
    @mock.patch.object(ServiceIndexer, 'index_item', autospec=True)
    @mock.patch.object(ServiceIndexer, 'request_items', autospec=True)
    def test_do_index_creates_service_indexer_class_and_indexes_items(self, request_items, index_item, indexer_init):
        indexer_init.return_value = None
        request_items.return_value = ['service1', 'service2']
        do_index(
            'services',
            "http://search-api-url", "mySearchAPIToken",
            "http://data-api-url", "myDataAPIToken",
            mapping=False,
            serial=True,  # don't run in parallel for testing
            index="myIndex",
            frameworks="framework1,framework2"
        )

        assert indexer_init.call_args_list == [
            mock.call(
                mock.ANY, 'services', self.data_api_client.return_value, self.search_api_client.return_value, 'myIndex'
            )
        ]
        # Both API clients initialised when the BriefIndexer instance is created
        assert self.data_api_client.call_args_list == [mock.call('http://data-api-url', 'myDataAPIToken')]
        assert self.search_api_client.call_args_list == [mock.call('http://search-api-url', 'mySearchAPIToken')]

        assert request_items.call_args_list == [
            mock.call(mock.ANY, "framework1,framework2")
        ]
        assert index_item.call_args_list == [
            mock.call(mock.ANY, 'service1'),
            mock.call(mock.ANY, 'service2'),
        ]
