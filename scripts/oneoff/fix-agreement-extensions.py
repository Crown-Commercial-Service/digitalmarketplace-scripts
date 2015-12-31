"""

Usage:
    scripts/oneoff/fix-agreement-extensions.py <stage> <api_token> <download_directory> [--dry-run]
"""
import sys
sys.path.insert(0, '.')

import os
import re

import magic
from docopt import docopt

from dmapiclient import DataAPIClient
from dmutils.s3 import S3
from dmscripts.env import get_api_endpoint_from_stage


def get_all_pdfs(download_directory):
    for root, subfolder, files in os.walk(download_directory):
        for filename in files:
            if filename.endswith('.pdf') and not filename.startswith('2015-11-'):
                yield os.path.join(root, filename)


def get_filetype(path):
    return magic.from_file(path, mime=True)


def is_empty(path):
    stat = os.stat(path)
    return stat.st_size == 0


def get_supplier_id_from_path(path):
    match = re.search(r'/(\d+)/', path)
    if not match:
        raise ValueError("Could not find supplier ID in path {}".format(path))
    return match.group(1)


def handle_path(client, bucket, dry_run, path):
    if is_empty(path):
        show_contact_details(client, dry_run, path)
    else:
        filetype = get_filetype(path)
        if filetype != b"application/pdf":
            update_file_extension(client, bucket, dry_run, path, filetype)


def show_contact_details(client, dry_run, path):
    supplier_id = get_supplier_id_from_path(path)
    if dry_run:
        print("Empty file for {} - {}".format(supplier_id, os.path.basename(path)))
    else:
        supplier = client.get_supplier(supplier_id)['suppliers']
        declaration = client.get_supplier_declaration(supplier_id, 'g-cloud-7')
        print(
            "Empty file for {}, {}, {}, {}".format(
                supplier_id,
                supplier['name'],
                declaration['declaration'].get('SQ1-2b', "none"),
                supplier['contactInformation'][0]['email']))


def get_correct_file_extension(filetype):
    extension = {
        b"application/zip": "zip",
        b"image/png": "png",
        b"image/jpeg": "jpg",
        b'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    }.get(filetype)
    if not extension:
        raise ValueError("Unknown file type: {}".format(filetype))
    return extension


def get_path_in_s3(path):
    return "{}/{}".format('g-cloud-7', path.split('/g-cloud-7/')[1])


def update_file_extension(client, bucket, dry_run, path, filetype):
    supplier_id = get_supplier_id_from_path(path)
    extension = get_correct_file_extension(filetype)
    path_in_s3 = get_path_in_s3(path)
    prefix, suffix = os.path.splitext(path_in_s3)
    new_path = "{}.{}".format(prefix, extension)
    if dry_run:
        print(
            "Not copying {} to {} for supplier {}".format(
                path_in_s3, new_path, supplier_id))
    else:
        print(
            "Copying {} to {} for supplier {} filetype {}".format(
                path_in_s3, new_path, supplier_id, filetype))
        bucket.bucket.copy_key(
            new_path,
            src_bucket_name=bucket.bucket_name,
            src_key_name=path_in_s3,
            metadata={'Content-Type': filetype.decode('utf-8')},
            preserve_acl=True,
        )
        client.register_framework_agreement_returned(
            supplier_id,
            'g-cloud-7',
            'script: fix incorrect extension'
        )


def get_bucket_name(stage):
    return 'digitalmarketplace-agreements-{0}-{0}'.format(stage)

if __name__ == '__main__':
    arguments = docopt(__doc__)

    stage = arguments['<stage>']
    api_token = arguments['<api_token>']
    download_directory = arguments['<download_directory>']
    dry_run = arguments['--dry-run']

    api_url = get_api_endpoint_from_stage(stage)

    if dry_run:
        client = None
        bucket = None
    else:
        client = DataAPIClient(api_url, api_token)
        bucket = S3(get_bucket_name(stage))

    for path in get_all_pdfs(download_directory):
        handle_path(client, bucket, dry_run, path)
