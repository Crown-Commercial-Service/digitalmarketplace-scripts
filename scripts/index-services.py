#!/usr/bin/env python
"""Read services from the API endpoint and write to search-api for indexing.

Usage:
    index-services.py <stage> --frameworks=<frameworks> --api-token=<api_access_token> \
--search-api-token=<search_api_access_token> [options]

    --serial                  Do not run in parallel (useful for debugging)
    --index=<index>           Search API index name [default: g-cloud-9]
    --frameworks=<frameworks> Comma-separated list of framework slugs that should be indexed

Example:
    ./index-services.py dev --api-token=myToken --search-api-token=myToken --frameworks=g-cloud-6,g-cloud-7"
"""

import sys
from datetime import datetime
from multiprocessing.pool import ThreadPool

import backoff
import dmapiclient
import six
from docopt import docopt
from six.moves import map

sys.path.insert(0, '.')
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging

logger = logging_helpers.configure_logger({"dmapiclient": logging.WARNING})


def request_services(api_url, api_access_token, frameworks):

    data_client = dmapiclient.DataAPIClient(
        api_url,
        api_access_token
    )

    return data_client.find_services_iter(framework=frameworks)


def print_progress(counter, start_time):
    if counter % 100 == 0:
        time_delta = datetime.utcnow() - start_time
        logger.info("{counter} in {time} ({rps}/s)", extra={
            'counter': counter, 'time': time_delta, 'rps': counter / time_delta.total_seconds()
        })


class ServiceIndexer(object):
    def __init__(self, endpoint, access_token, index):
        self.endpoint = endpoint
        self.access_token = access_token
        self.index = index

    def __call__(self, service):
        client = dmapiclient.SearchAPIClient(self.endpoint, self.access_token)

        try:
            self.index_service(client, service)
            return True
        except dmapiclient.APIError:
            logger.exception("{service_id} not indexed", extra={'service_id': service.get('id')})
            return False

    @backoff.on_exception(backoff.expo, dmapiclient.HTTPError, max_tries=5)
    def index_service(self, client, service):
        if service['status'] == 'published':
            client.index(service['id'], service, index=self.index)
        else:
            client.delete(service['id'], index=self.index)

    def create_index(self):
        client = dmapiclient.SearchAPIClient(self.endpoint, self.access_token)
        logger.info("Creating {index} index", extra={'index': self.index})

        try:
            result = client.create_index(self.index)
            logger.info("Index creation response: {response}", extra={'response': result})
        except dmapiclient.HTTPError as e:
            if 'already exists as alias' in e.message:
                logger.info("Skipping index creation for alias {index}", extra={'index': self.index})
            else:
                raise


def do_index(search_api_url, search_api_access_token, data_api_url, data_api_access_token, serial, index, frameworks):
    logger.info("Search API URL: {search_api_url}", extra={'search_api_url': search_api_url})
    logger.info("Data API URL: {data_api_url}", extra={'data_api_url': data_api_url})

    if serial:
        pool = None
        mapper = map
    else:
        pool = ThreadPool(10)
        mapper = pool.imap_unordered

    indexer = ServiceIndexer(search_api_url, search_api_access_token, index)
    indexer.create_index()

    counter = 0
    start_time = datetime.utcnow()
    status = True

    services = request_services(data_api_url, data_api_access_token, frameworks)
    for result in mapper(indexer, services):
        counter += 1
        status = status and result
        print_progress(counter, start_time)

    return status

if __name__ == "__main__":
    arguments = docopt(__doc__)
    ok = do_index(
        data_api_url=get_api_endpoint_from_stage(arguments['<stage>'], 'api'),
        data_api_access_token=arguments['--api-token'],
        search_api_url=get_api_endpoint_from_stage(arguments['<stage>'], 'search-api'),
        search_api_access_token=arguments['--search-api-token'],
        serial=arguments['--serial'],
        index=arguments['--index'],
        frameworks=arguments['--frameworks']
    )

    if not ok:
        sys.exit(1)
