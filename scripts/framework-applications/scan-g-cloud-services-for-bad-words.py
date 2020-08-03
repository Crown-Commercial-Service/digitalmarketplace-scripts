#!/usr/bin/env python

"""
This script will check all free-text fields in submitted G-Cloud services for "bad words", as defined in
the file at <bad_words_path> (typically block-list.txt in https://github.com/alphagov/digitalmarketplace-bad-words),
and generate a CSV report of any bad word found.

Use the --scan-drafts option to scan draft services (supplier must still have 'onFramework' set to True).

Usage:
    scripts/framework-applications/scan-g-cloud-services-for-bad-words.py <stage> <frameworks-repo-root-dir>
        <bad_words_path> <framework_slug> <output_dir> [--scan-drafts]
"""
import os
import sys

sys.path.insert(0, '.')

from docopt import docopt
from dmcontent.content_loader import ContentLoader
from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage

from dmscripts.scan_g_cloud_services_for_bad_words import scan_services_for_bad_words
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging


logger = logging_helpers.configure_logger({"dmapiclient": logging.WARNING})


if __name__ == '__main__':
    arguments = docopt(__doc__)
    api_url = get_api_endpoint_from_stage(arguments['<stage>'])
    client = DataAPIClient(api_url, get_auth_token('api', arguments['<stage>']))

    content_repo_path = arguments['<frameworks-repo-root-dir>']
    if not os.path.exists(content_repo_path):
        logger.error('Cannot find path to frameworks repo at', content_repo_path)
        exit(1)
    content_loader = ContentLoader(content_repo_path)

    bad_words_path = arguments['<bad_words_path>']
    if not os.path.exists(bad_words_path):
        logger.error('Cannot find path to bad words file at', bad_words_path)
        exit(1)

    output_dir = arguments['<output_dir>']
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    bad_word_counts = scan_services_for_bad_words(
        client,
        bad_words_path,
        arguments['<framework_slug>'],
        output_dir,
        content_loader,
        logger,
        scan_drafts=arguments['--scan-drafts']
    )
    logger.info("BAD WORD COUNTS: {}".format(bad_word_counts))
