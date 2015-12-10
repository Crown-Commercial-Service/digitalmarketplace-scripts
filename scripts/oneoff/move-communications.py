#!/usr/bin/env python
"""Move communications files from g7 draft documents to communications bucket

Usage:
    scripts/oneoff/move-communications.py <stage>
"""
import sys
sys.path.insert(0, '.')

import re
from docopt import docopt

from dmutils.s3 import S3


def make_copier(src_bucket, target_bucket):
    def copy_file(src_path, target_path):
        src_key = src_bucket.bucket.get_key(src_path)
        target_bucket.bucket.copy_key(
            target_path,
            src_bucket_name=src_bucket.bucket_name,
            src_key_name=src_path,
            preserve_acl=True,
            metadata={
                "timestamp": src_key.last_modified
            }
        )

    return copy_file


def main(stage):
    drafts_bucket_name = 'digitalmarketplace-g7-draft-documents-{0}-{0}'.format(stage)
    communications_bucket_name = 'digitalmarketplace-communications-{0}-{0}'.format(stage)

    drafts_bucket = S3(drafts_bucket_name)
    communications_bucket = S3(communications_bucket_name)

    copy_file = make_copier(drafts_bucket, communications_bucket)

    copy_file(
        "g-cloud-7-supplier-pack.zip",
        "g-cloud-7/communications/g-cloud-7-supplier-pack.zip")
    for file in drafts_bucket.list('g-cloud-7-updates'):
        newpath = "g-cloud-7/communications/updates/{}".format(
            re.sub(r'^g-cloud-7-updates/', '', file['path'])
        )
        copy_file(file['path'], newpath)


if __name__ == '__main__':
    arguments = docopt(__doc__)
    stage = arguments['<stage>']

    main(stage)
