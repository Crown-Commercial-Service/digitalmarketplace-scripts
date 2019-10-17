from datetime import datetime
from itertools import chain
from multiprocessing.pool import ThreadPool

import dmapiclient
from six.moves import map

from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging

logger = logging_helpers.configure_logger({"dmapiclient": logging.WARNING})


def print_progress(counter, start_time):
    if counter % 100 == 0:
        time_delta = datetime.utcnow() - start_time
        logger.info("{counter} in {time} ({rps}/s)", extra={
            'counter': counter, 'time': time_delta, 'rps': counter / time_delta.total_seconds()
        })


class IndexerBase(object):
    def __init__(self, document_type, data_client, search_client, index):
        self.document_type = document_type
        self.index = index
        self.search_client = search_client
        self.data_client = data_client

    def create_index(self, mapping):
        logger.info("Creating {index} index", extra={'index': self.index})

        try:
            result = self.search_client.create_index(self.index, mapping=mapping)
            logger.info("Index creation response: {response}", extra={'response': result})
        except dmapiclient.HTTPError as e:
            if 'already exists as alias' in str(e.message):
                logger.info("Skipping index creation for alias {index}", extra={'index': self.index})
            else:
                raise

    def request_items(self, frameworks):
        raise NotImplementedError()

    def __call__(self, item):
        try:
            self.index_item(item)
            return True
        except dmapiclient.APIError:
            logger.exception("{id} not indexed", extra={'id': item.get('id')})
            return False

    def include_in_index(self, item):
        raise NotImplementedError()

    def index_item(self, item):
        if self.include_in_index(item):
            self.search_client.index(self.index, item['id'], item, self.document_type)
        else:
            self.search_client.delete(self.index, item['id'])


class BriefIndexer(IndexerBase):
    def request_items(self, frameworks):
        # this is done as two separate calls because the bulk of the results should be deliverable in a compressed
        # response (which we want as it tends to be more reliable), however we still need to send "withdrawn" briefs
        # to the search api as this is the only way such briefs get removed from the search results. the api will
        # likely refuse to compress these but that's fine as there aren't many of them.
        return chain(
            self.data_client.find_briefs_iter(
                framework=frameworks,
                status="live,cancelled,unsuccessful,awarded,closed",
            ),
            self.data_client.find_briefs_iter(framework=frameworks, status="withdrawn"),
        )

    def include_in_index(self, item):
        # Even draft briefs will be in the index, for now at least
        return True


class ServiceIndexer(IndexerBase):
    def request_items(self, frameworks):
        # despite the name, frameworks takes a string containing a comma-separated list of framework slugs
        return self.data_client.find_services_iter(framework=frameworks)

    def include_in_index(self, item):
        return item['status'] == 'published'


indexers = {
    'briefs': BriefIndexer,
    'services': ServiceIndexer,
}


# Hardcoded for now as we are unlikely to add new frameworks in the near future
GCLOUD_MAPPINGS = {
    'g-cloud-9': 'services',
    'g-cloud-10': 'services-g-cloud-10',
    'g-cloud-11': 'services-g-cloud-11'
}
# All DOS framework iterations use the same mapping, which was last changed for DOS2
DOS_MAPPING = 'briefs-digital-outcomes-and-specialists-2'


def search_mapping_matches_framework(mapping_name, frameworks):
    # Check that the mapping has been generated from at least one of the frameworks given in
    # the comma-separated list
    framework_list = frameworks.split(',')
    for fw in framework_list:
        if 'digital-outcomes-and-specialists' in fw and mapping_name == DOS_MAPPING:
            return True
        elif mapping_name == GCLOUD_MAPPINGS.get(fw):
            return True
    raise ValueError("Incorrect mapping '{}' for the supplied framework(s): {}".format(mapping_name, frameworks))


def do_index(doc_type, search_api_url, search_api_access_token, data_api_url, data_api_access_token, mapping, serial,
             index, frameworks):
    logger.info("Search API URL: {search_api_url}", extra={'search_api_url': search_api_url})
    logger.info("Data API URL: {data_api_url}", extra={'data_api_url': data_api_url})

    if serial:
        mapper = map
    else:
        pool = ThreadPool(10)
        mapper = pool.imap_unordered

    indexer = indexers[doc_type](
        doc_type,
        dmapiclient.DataAPIClient(data_api_url, data_api_access_token),
        dmapiclient.SearchAPIClient(search_api_url, search_api_access_token),
        index)
    if mapping and search_mapping_matches_framework(mapping, frameworks):
        indexer.create_index(mapping=mapping)

    counter = 0
    start_time = datetime.utcnow()
    status = True
    items = indexer.request_items(frameworks)
    for result in mapper(indexer, items):
        counter += 1
        status = status and result
        print_progress(counter, start_time)

    return status
