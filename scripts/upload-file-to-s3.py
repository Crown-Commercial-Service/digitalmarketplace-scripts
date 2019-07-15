#!/usr/bin/env python3
"""
Usage:
    scripts/upload-file-to-s3.py
        <file_path> <bucket_name> <remote_key_name> [<remote_name>] [--dry-run] [--public]

Options:
    -h --help   Show this screen.
    --file_path=<file_path>  Local path of file to be saved in S3
    --bucket_name=<bucket_name>  Bucket category, used to get name ie agreements/ communications/ documents
    --remote_key_name=<remote_key_name>
        AWS S3 requires a key name, this is often a path like string eg. data/files/myfile.txt
    --download_name=<download_name>
        Suggested name for a browser to download this file as, part of Content-Disposition header.
        Content-Disposition will only be added if the argument is provided.
        If this is a file for download, provide it.
    --dry-run  Don't actually perform the upload
    --public  Trigger the public-read acl option, defaults to private
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt

from dmutils.s3 import S3


if __name__ == '__main__':
    arguments = docopt(__doc__)

    # Get arguments
    file_path = arguments['<file_path>']
    bucket_name = arguments['<bucket_name>']
    remote_key_name = arguments['<remote_key_name>']
    download_name = arguments.get('<remote_name>', None)
    dry_run = arguments['--dry-run']
    public = arguments['--public']

    # Set defaults
    acl = 'public-read' if public else 'private'

    # Grab bucket
    bucket = S3(bucket_name)
    # Open file
    with open(file_path, 'br') as source_file:
        if not dry_run:
            # Save file
            bucket.save(remote_key_name, source_file, acl=acl, download_filename=download_name)
        print("{}UPLOAD: {} to {}::{} as {}".format(
            '[Dry-run]' if dry_run else '',
            file_path,
            bucket.bucket_name,
            remote_key_name,
            download_name
        ))
