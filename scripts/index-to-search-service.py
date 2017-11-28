#!/usr/bin/env python
"""Read services from the API endpoint and write to search-api for indexing.

Usage:
    index-to-search-service.py <doc-type> <stage> [--create] --index=<index> --frameworks=<frameworks> \
--mapping=<mapping> [options]

    <doc-type>                                    One of briefs or services
    <stage>                                       One of dev, preview, staging or production
    --create                                      Use this flag to create the index if it doesn't exist. If it does
                                                  exist, the mapping for the index will be updated. Don't specify this
                                                  option when running from a batch/Jenkins job, as both creating indexes
                                                  and updating mappings should be done under user control.
    --index=<index>                               Search API index name, usually of the form <framework>-YYYY-MM-DD
    --frameworks=<frameworks>                     Comma-separated list of framework slugs that should be indexed
    --mapping=<mapping>                           One of the mappings supported by the Search API.

Options:
    --serial                                      Do not run in parallel (useful for debugging)
    --api-url=<api-url>                           Override API URL (otherwise automatically populated)
    --api-token=<api_access_token>                Override API token (otherwise automatically populated)
    --search-api-url=<search-api-url>             Override search API URL (otherwise automatically populated)
    --search-api-token=<search_api_access_token>  Override search API token (otherwise automatically populated)

Example:
    ./index-to-search-service.py services dev --index=g-cloud-9-2017-10-17 --frameworks=g-cloud-9 \
--mapping=g-cloud-9-services
"""

import sys
from datetime import datetime
from multiprocessing.pool import ThreadPool

import backoff
import dmapiclient
from docopt import docopt
from six.moves import map


sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
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

    @backoff.on_exception(backoff.expo, dmapiclient.HTTPError, max_tries=5)
    def index_item(self, item):
        if self.include_in_index(item):
            self.search_client.index(self.index, item['id'], item, self.document_type)
        else:
            self.search_client.delete(self.index, item['id'])


class BriefIndexer(IndexerBase):
    def request_items(self, frameworks):
        # despite the name, `framework` takes a string containing a comma-separated list of framework slugs
        return self.data_client.find_briefs_iter(framework=frameworks)

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


def do_index(doc_type, search_api_url, search_api_access_token, data_api_url, data_api_access_token, mapping, serial,
             index, frameworks, create_index):
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
    if create_index:
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


if __name__ == "__main__":
    arguments = docopt(__doc__)
    ok = do_index(
        doc_type=arguments['<doc-type>'],
        data_api_url=arguments['--api-url'] or get_api_endpoint_from_stage(arguments['<stage>'], 'api'),
        data_api_access_token=arguments['--api-token'] or get_auth_token('api', arguments['<stage>']),
        search_api_url=arguments['--search-api-url'] or get_api_endpoint_from_stage(arguments['<stage>'], 'search-api'),
        search_api_access_token=arguments['--search-api-token'] or get_auth_token('search_api', arguments['<stage>']),
        mapping=arguments['--mapping'],
        serial=arguments['--serial'],
        index=arguments['--index'],
        frameworks=arguments['--frameworks'],
        create_index=arguments['--create']
    )

    if not ok:
        sys.exit(1)
