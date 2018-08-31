#!/usr/bin/env python
"""Read services from the API endpoint and write to search-api for indexing.

Usage:
    index-to-search-service.py <doc-type> <stage> --index=<index> --frameworks=<frameworks> [options]

    <doc-type>                                    One of briefs or services
    <stage>                                       One of dev, preview, staging or production
    --index=<index>                               Search API index name, usually of the form <framework>-YYYY-MM-DD
    --frameworks=<frameworks>                     Comma-separated list of framework slugs that should be indexed

Options:
    -h --help                                     Show this screen.
    --create-with-mapping=<mapping>               Create the named index using mapping <mapping>. Don't specify this
                                                  option when running from a batch/Jenkins job, as creating indexes
                                                  should be done under user control. This mapping is a filename (without
                                                  .json suffix) as would be found by the search-api in its
                                                  digitalmarketplace-search-api/mappings directory.
    --serial                                      Do not run in parallel (useful for debugging)
    --api-url=<api-url>                           Override API URL (otherwise automatically populated)
    --api-token=<api_access_token>                Override API token (otherwise automatically populated)
    --search-api-url=<search-api-url>             Override search API URL (otherwise automatically populated)
    --search-api-token=<search_api_access_token>  Override search API token (otherwise automatically populated)

Examples:
    ./scripts/index-to-search-service.py services dev --index=g-cloud-9-2017-10-17 --frameworks=g-cloud-9 \
--create-with-mapping=services

    ./scripts/index-to-search-service.py briefs dev --index=briefs-digital-outcomes-and-specialists-2017-10-17 \
--frameworks=digital-outcomes-and-specialists-2 --create-with-mapping=briefs-digital-outcomes-and-specialists-2
"""

import sys
from docopt import docopt

sys.path.insert(0, '.')
from dmscripts.index_to_search_service import do_index
from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage


if __name__ == "__main__":
    arguments = docopt(__doc__)
    ok = do_index(
        doc_type=arguments['<doc-type>'],
        data_api_url=arguments['--api-url'] or get_api_endpoint_from_stage(arguments['<stage>'], 'api'),
        data_api_access_token=arguments['--api-token'] or get_auth_token('api', arguments['<stage>']),
        search_api_url=arguments['--search-api-url'] or get_api_endpoint_from_stage(arguments['<stage>'], 'search-api'),
        search_api_access_token=arguments['--search-api-token'] or get_auth_token('search_api', arguments['<stage>']),
        mapping=arguments.get('--create-with-mapping'),
        serial=arguments['--serial'],
        index=arguments['--index'],
        frameworks=arguments['--frameworks'],
    )

    if not ok:
        sys.exit(1)
