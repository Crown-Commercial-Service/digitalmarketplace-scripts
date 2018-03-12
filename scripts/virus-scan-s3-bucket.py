#!/usr/bin/env python3
"""Virus scan the contents of an S3 bucket, optionally from a given date onwards.
Requires a clamd backend to be provided (e.g. https://github.com/UKHomeOffice/docker-clamav)

You'll need to configure the required AWS environment variables, normally either AWS_PROFILE, or
AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY.

Example:
    ./scripts/virus-scan-s3-bucket.py --since 2018-01-01T00:00:00Z --prefix g-cloud-9/documents \
        digitalmarketplace-dev-uploads
"""

import argparse
import clamd
import dateutil.parser as dateutil_parser
import logging
import io
import sys

sys.path.insert(0, '.')  # noqa

from dmutils.s3 import S3
from dmscripts.helpers.logging_helpers import INFO, configure_logger


logger = logging.getLogger("script")


def virus_scan_bucket(s3, clam, prefix, since, dry_run=True):
    scanned_files, clean, infected = 0, 0, 0

    # s3.list can block for a significant amount of time against large buckets when loading with timestamps. During
    # this time there will be no output.
    logger.info('Gathering objects. This may take some time depending on the size of the bucket ...')
    for file_meta in s3.list(prefix=prefix, load_timestamps=True):
        if since and file_meta.get('last_modified') and dateutil_parser.parse(file_meta['last_modified']) < since:
            logger.info(f'Ignoring file from {file_meta["last_modified"]}: {file_meta["path"]}')
            continue

        logger.info(f'Processing file from {file_meta["last_modified"]}: {file_meta["path"]}')

        with io.BytesIO() as file_buffer:
            if not dry_run:
                s3._bucket.download_fileobj(Key=file_meta['path'], Fileobj=file_buffer)

            file_buffer.seek(0)
            scanned_files += 1
            result = clam.instream(file_buffer)

            if result['stream'][0] == 'OK':
                logger.info(f'Result: {result["stream"][0]}, {result["stream"][1]}')
                clean += 1
            else:
                logger.warning(f'Result: {result["stream"][0]}, {result["stream"][1]}')
                infected += 1

    logger.info(f'')
    logger.info(f' Total files scanned: {scanned_files}')
    logger.info(f'   Total clean files: {clean}')
    logger.info(f'Total infected files: {infected}')

    sys.exit(infected)


if __name__ == '__main__':
    configure_logger({"script": INFO})

    a = argparse.ArgumentParser()
    a.add_argument('bucket',
                   type=str,
                   help='The s3 bucket to use (e.g. `digitalmarketplace-dev-uploads`).')
    a.add_argument('--prefix',
                   default='',
                   type=str,
                   help='The s3 object prefix to filter on (e.g. `g-cloud-9/documents/`).')
    a.add_argument('--host',
                   default='localhost',
                   type=str,
                   help='The exposed host on which clamd is available (default: `localhost`).')
    a.add_argument('--port',
                   default=3310,
                   type=int,
                   help='The exposed port on which clamd is available (default: 3310).')
    a.add_argument('--since',
                   type=dateutil_parser.parse,
                   help='A timezone-aware ISO8601 datetime string; if provided, only scan objects uploaded after '
                        'this point in time (Example: 2018-01-01T12:00:00Z).')
    a.add_argument('--dry-run',
                   action='store_true',
                   default=False,
                   help='Perform a dry run - will bypass downloading and scanning files from S3.')

    args = a.parse_args()

    if args.since and not args.since.tzinfo:
        logger.error('You must supply a timezone-aware ISO8601 datetime string. You probably just need to append `Z`'
                     'to the end of your datetime string. Example: 2018-01-01T12:00:00Z')
        sys.exit(-1)

    s3 = S3(bucket_name=args.bucket)
    clam = clamd.ClamdNetworkSocket(host=args.host, port=args.port)

    try:
        pong = clam.ping()
        if pong != 'PONG':
            raise clamd.ConnectionError(f'Invalid ping response: {pong}')

    except clamd.ConnectionError as e:
        logger.error(f'Clamd backend not responding to ping: {e}')
        sys.exit(-2)

    logger.info(f' Configuration:')
    logger.info(f' Target bucket: {args.bucket}')
    logger.info(f' Filter prefix: {args.prefix}')
    logger.info(f'Modified since: {args.since}')
    logger.info(f'ClamAV backend: {args.host}:{args.port}')
    logger.info(f'       Dry run: {args.dry_run}')

    virus_scan_bucket(s3=s3, clam=clam, prefix=args.prefix, since=args.since, dry_run=args.dry_run)
