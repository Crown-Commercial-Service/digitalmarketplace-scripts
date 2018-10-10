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
import dateutil.parser as dateutil_parser
from itertools import chain
import logging
import sys

import boto3

from dmapiclient import AntivirusAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage

sys.path.insert(0, '.')

from dmscripts.helpers.logging_helpers import DEBUG, INFO, configure_logger
from dmscripts.helpers.auth_helpers import get_auth_token


logger = logging.getLogger("script")


def virus_scan_bucket(s3_client, antivirus_api_client, bucket_name, prefix="", since=None, dry_run=True):
    candidate_count, pass_count, fail_count, already_tagged_count = 0, 0, 0, 0

    for version in chain.from_iterable(
        page.get("Versions") or ()
        for page in s3_client.get_paginator("list_object_versions").paginate(
            Bucket=bucket_name,
            Prefix=prefix,
        )
    ):
        if since and version.get('LastModified') and version['LastModified'] < since:
            logger.debug("Ignoring file from %s: %s", version["LastModified"], version["Key"])
            continue

        logger.info(
            f"{'(Would be) ' if dry_run else ''}Requesting scan of key %s version %s (%s)",
            version["Key"],
            version["VersionId"],
            version["LastModified"],
        )
        candidate_count += 1

        if not dry_run:
            result = antivirus_api_client.scan_and_tag_s3_object(
                bucket_name,
                version["Key"],
                version["VersionId"],
            )

            if result["avStatusApplied"]:
                if result.get("newAvStatus", {}).get("avStatus.result") == "pass":
                    pass_count += 1
                else:
                    fail_count += 1
                message = f"Marked with result {result.get('newAvStatus', {}).get('avStatus.result')}"
            else:
                already_tagged_count += 1
                message = f"Unchanged: "
                if result.get("existingAvStatus", {}).get("avStatus.result"):
                    message += f"already marked as {result['existingAvStatus']['avStatus.result']!r}"
                    if result.get("existingAvStatus", {}).get("avStatus.ts"):
                        message += f" ({result['existingAvStatus']['avStatus.ts']})"

            logger.info("%s: %s", version["VersionId"], message)

    return candidate_count, pass_count, fail_count, already_tagged_count


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('stage',
                   type=str,
                   help='One of dev, preview, staging or production')
    a.add_argument('bucket',
                   type=str,
                   help='The s3 bucket to use (e.g. `digitalmarketplace-dev-uploads`).')
    a.add_argument('--prefix',
                   default='',
                   type=str,
                   help='The s3 object prefix to filter on (e.g. `g-cloud-9/documents/`).')
    a.add_argument('--since',
                   type=dateutil_parser.parse,
                   help='A timezone-aware ISO8601 datetime string; if provided, only scan objects uploaded after '
                        'this point in time (Example: 2018-01-01T12:00:00Z).')
    a.add_argument('--dry-run',
                   action='store_true',
                   default=False,
                   help='Perform a dry run - will bypass requesting scan from antivirus api')
    a.add_argument('--verbose',
                   action='store_true',
                   default=False,
                   help='Output more verbose progress information')

    args = a.parse_args()

    configure_logger({"script": DEBUG if args.verbose else INFO})

    if args.since and not args.since.tzinfo:
        logger.error('You must supply a timezone-aware ISO8601 datetime string. You probably just need to append `Z`'
                     'to the end of your datetime string. Example: 2018-01-01T12:00:00Z')
        sys.exit(-1)

    av_api_client = AntivirusAPIClient(
        get_api_endpoint_from_stage(args.stage, "antivirus-api"),
        get_auth_token("antivirus_api", args.stage),
    )

    logger.info(
        "Configuration:\nTarget stage:\t%s\nTarget bucket:\t%s\nFilter prefix:\t%s\nModified since:\t%s\nDry run:\t%s",
        args.stage,
        args.bucket,
        args.prefix,
        args.since,
        args.dry_run,
    )

    candidate_count, pass_count, fail_count, already_tagged_count = virus_scan_bucket(
        s3_client=boto3.client("s3", region_name="eu-west-1"),  # actual region specified here doesn't matter
        antivirus_api_client=av_api_client,
        bucket_name=args.bucket,
        prefix=args.prefix,
        since=args.since,
        dry_run=args.dry_run,
    )

    logger.info(
        "Total files found:\t%s\nTotal files passed:\t%s\nTotal files failed:\t%s\nTotal files already tagged:\t%s",
        candidate_count,
        pass_count,
        fail_count,
        already_tagged_count,
    )

    sys.exit(fail_count)
