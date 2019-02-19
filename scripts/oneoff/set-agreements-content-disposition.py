#!/usr/bin/env python
"""Removes supplier name from existing agreement file names and adds a download filename header.

Usage:
    scripts/oneoff/set-agreements-content-disposition.py <stage>

"""
import sys
sys.path.insert(0, '.')

import re
from docopt import docopt
from dateutil.parser import parse as parse_time

from dmutils.s3 import S3
from dmutils.formats import DATETIME_FORMAT

from dmscripts.helpers import logging_helpers

logger = logging_helpers.configure_logger()


def make_copier(src_bucket, target_bucket):
    def copy_file_with_content_disposition(src_path, target_path, download_filename):
        src_key = src_bucket.bucket.get_key(src_path)
        target_bucket.bucket.copy_key(
            target_path,
            src_bucket_name=src_bucket.bucket_name,
            src_key_name=src_path,
            preserve_acl=True,
            metadata={
                "timestamp": parse_time(src_key.last_modified).strftime(DATETIME_FORMAT),
                "Content-Disposition": 'attachment; filename="{}"'.format(download_filename),
            }
        )

    return copy_file_with_content_disposition


def path_without_supplier_name(path):
    folder, _, filename = path.rpartition('/')

    # Skip archived file versions starting with timestamps
    if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}', filename):
        logger.info("Skipping old file version {}".format(path))
        return None, None

    # Find filenames starting with a supplier name prefix and remove it
    match = re.search(r'-(\d{5,6}-.*)', filename)
    if not match:
        logger.info("{} does not match pattern".format(path))
        return None, None
    return "/".join([folder, match.group(1)]), filename


def main(stage):
    agreements_bucket_name = 'digitalmarketplace-agreements-{0}-{0}'.format(stage)

    agreements_bucket = S3(agreements_bucket_name)
    copy_file = make_copier(agreements_bucket, agreements_bucket)

    agreements_files = agreements_bucket.list('g-cloud-7/agreements/')
    for key in agreements_files:
        new_path, download_filename = path_without_supplier_name(key['path'])
        if not new_path:
            continue

        if any(k['path'] == new_path for k in agreements_files):
            logger.info("Not replacing %s, file already exists", new_path)
            continue

        logger.info("Copying '%s' to '%s' with filename '%s'", key['path'], new_path, download_filename)

        copy_file(key['path'], new_path, download_filename=download_filename)


if __name__ == '__main__':
    arguments = docopt(__doc__)
    stage = arguments['<stage>']

    main(stage)
