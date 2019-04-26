import os
import re
import csv

from dmutils.documents import get_document_path, generate_download_filename

BUCKET_CATEGORIES = [
    'agreements',
    'communications',
    'documents',
    'submissions'
]


def upload_file(bucket, dry_run, file_path, framework_slug, bucket_category,
                document_category=None, document_type=None, supplier_name_dict=None):
    supplier_id = get_supplier_id_from_framework_file_path(file_path)
    if document_category is None:
        document_name = get_document_name_from_file_path(file_path)
    else:
        document_name = '{0}.{1}'.format(document_category, document_type)
    if 'signed-framework-agreement' in document_name:
        print('Signed and countersigned agreement paths now need to be stored in database so can no longer be uploaded '
              'using this script.')
        return
    upload_path = get_document_path(framework_slug, supplier_id, bucket_category,
                                    document_name)
    if supplier_name_dict is None:
        download_filename = None
    else:
        supplier_name = supplier_name_dict[supplier_id]
        download_filename = generate_download_filename(
            supplier_id, document_name, supplier_name)
    if not dry_run:
        with open(file_path, 'rb') as source_file:
            bucket.save(upload_path, source_file, acl='bucket-owner-full-control', download_filename=download_filename)
        print(supplier_id)
    else:
        print("[Dry-run] UPLOAD: '{}' to '{}'".format(file_path, upload_path))


def get_bucket_name(stage, bucket_category):
    if bucket_category not in BUCKET_CATEGORIES:
        return None
    if stage in ['local', 'dev']:
        return "digitalmarketplace-dev-uploads"
    if stage not in ['preview', 'staging', 'production']:
        return None

    bucket_name = 'digitalmarketplace-{0}-{1}-{1}'.format(bucket_category, stage)
    print("BUCKET: {}".format(bucket_name))
    return bucket_name


def get_all_files_of_type(local_directory, file_type):
    for root, subfolder, files in os.walk(local_directory):
        for filename in files:
            if filename.endswith(file_type):
                yield os.path.join(root, filename)


def get_supplier_id_from_framework_file_path(path):
    match = re.search(r'(?:/|-)(\d{5,6})[-_]', path)
    if not match:
        raise ValueError("Could not find supplier ID in path {}".format(path))
    return match.group(1)


def get_document_name_from_file_path(path):
    match = re.search(r'/\d{5,6}-(.*)', path)
    return match.group(1)


def get_supplier_name_dict_from_tsv(tsv_path):
    suppliers_name_dict = {}
    with open(tsv_path, 'r') as tsvfile:
        tsv_reader = csv.reader(tsvfile, delimiter='\t')
        for row in tsv_reader:
            suppliers_name_dict[row[0]] = row[1]
    return suppliers_name_dict
