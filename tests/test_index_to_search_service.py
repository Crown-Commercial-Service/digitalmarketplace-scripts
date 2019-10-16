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
        self.data_api_client.return_value.find_briefs_iter.side_effect = lambda *args, **kwargs: {
            "live,cancelled,unsuccessful,awarded,closed": iter(('brief1', 'brief2',)),
            "withdrawn": iter(('brief3',)),
        }[kwargs.get("status")]
        indexer = BriefIndexer(
            'briefs', self.data_api_client.return_value, self.search_api_client.return_value, 'myIndex'
        )
        assert tuple(indexer.request_items('framework1,framework2')) == ('brief1', 'brief2', 'brief3',)
        assert self.data_api_client.mock_calls == [
            mock.call().find_briefs_iter(
                framework='framework1,framework2',
                status="live,cancelled,unsuccessful,awarded,closed",
            ),
            mock.call().find_briefs_iter(
                framework='framework1,framework2',
                status="withdrawn",
            ),
        ]

    def test_service_indexer_request_items_calls_data_api_client_with_frameworks(self):
        self.data_api_client.return_value.find_services_iter.return_value = iter(('service1', 'service2',))
        indexer = ServiceIndexer(
            'services', self.data_api_client.return_value, self.search_api_client.return_value, 'myIndex'
        )
        assert tuple(indexer.request_items('framework1,framework2')) == ('service1', 'service2',)
        assert self.data_api_client.return_value.find_services_iter.call_args_list == [
            mock.call(framework='framework1,framework2')
        ]

    def test_brief_indexer_index_items_calls_search_api_client(self):
        self.data_api_client.return_value.find_briefs_iter.side_effect = lambda *args, **kwargs: {
            "live,cancelled,unsuccessful,awarded,closed": iter(('brief1', 'brief2',)),
            "withdrawn": iter(('brief3',)),
        }[kwargs.get("status")]
        indexer = BriefIndexer(
            'briefs', self.data_api_client.return_value, self.search_api_client.return_value, 'myIndex'
        )
        indexer.index_item({'id': 'newBrief'})
        assert self.search_api_client.return_value.index.call_args_list == [
            mock.call('myIndex', 'newBrief', {'id': 'newBrief'}, 'briefs')
        ]

    def test_service_indexer_index_items_calls_search_api_index_for_published_services(self):
        self.data_api_client.return_value.find_services_iter.return_value = iter(('service1', 'service2',))
        indexer = ServiceIndexer(
            'services', self.data_api_client.return_value, self.search_api_client.return_value, 'myIndex'
        )

        indexer.index_item({'id': 'newService', 'status': 'published'})
        assert self.search_api_client.return_value.index.call_args_list == [
            mock.call('myIndex', 'newService', {'id': 'newService', 'status': 'published'}, 'services')
        ]

    def test_service_indexer_index_items_calls_search_api_delete_for_published_services(self):
        self.data_api_client.return_value.find_services_iter.return_value = iter(('service1', 'service2',))
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
        request_items.return_value = iter(('brief1', 'brief2',))
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
        request_items.return_value = iter(('service1', 'service2',))
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

    @mock.patch.object(ServiceIndexer, 'create_index', autospec=True)
    def test_do_index_creates_new_index_from_services_mapping(self, create_index):
        do_index(
            'services',
            "http://search-api-url", "mySearchAPIToken",
            "http://data-api-url", "myDataAPIToken",
            mapping='services-g-cloud-10',
            serial=True,  # don't run in parallel for testing
            index="my-new-g-cloud-10-index",
            frameworks="g-cloud-10"
        )

        assert create_index.call_args_list == [
            mock.call(mock.ANY, mapping='services-g-cloud-10')
        ]

    @pytest.mark.parametrize(
        'framework_list',
        [
            "digital-outcomes-and-specialists",
            "digital-outcomes-and-specialists,digital-outcomes-and-specialists-2",
            "digital-outcomes-and-specialists,digital-outcomes-and-specialists-99",
            "digital-outcomes-and-specialists-99",
        ]
    )
    @mock.patch.object(BriefIndexer, 'create_index', autospec=True)
    def test_do_index_creates_new_index_from_briefs_mapping_for_dos_frameworks(self, create_index, framework_list):
        do_index(
            'briefs',
            "http://search-api-url", "mySearchAPIToken",
            "http://data-api-url", "myDataAPIToken",
            mapping='briefs-digital-outcomes-and-specialists-2',
            serial=True,  # don't run in parallel for testing
            index="my-new-dos-index",
            frameworks=framework_list
        )

        assert create_index.call_args_list == [
            mock.call(mock.ANY, mapping='briefs-digital-outcomes-and-specialists-2')
        ]

    @mock.patch.object(ServiceIndexer, 'create_index', autospec=True)
    def test_incorrect_mapping_for_framework_raises_error(self, create_index):
        with pytest.raises(ValueError) as e:
            do_index(
                'services',
                "http://search-api-url", "mySearchAPIToken",
                "http://data-api-url", "myDataAPIToken",
                mapping='services',
                serial=True,  # don't run in parallel for testing
                index="my-new-g-cloud-10-index",
                frameworks="g-cloud-10"
            )

        assert str(e.value) == "Incorrect mapping 'services' for the supplied framework(s): g-cloud-10"

        assert create_index.call_args_list == []
