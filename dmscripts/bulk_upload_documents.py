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


def upload_file(bucket, dry_run, file_path, framework_slug, bucket_category, supplier_name_dict=None):
    # Retrieve the supplier ID from the filepath
    supplier_id = get_supplier_id_from_framework_file_path(file_path)

    # Construct the document name
    document_name = get_document_name_from_file_path(file_path)

    # Don't upload signed agreement files
    if 'signed-framework-agreement' in document_name:
        raise ValueError(
            f"'{document_name}'. Signed and countersigned agreement documents should not be uploaded "
            f"using this script as they require the document URL to be stored in the database."
        )

    # Construct the upload path
    upload_path = get_document_path(framework_slug, supplier_id, bucket_category, document_name)

    # Get the download_filename if TSV supplied
    if supplier_name_dict is None:
        download_filename = None
    else:
        supplier_name = supplier_name_dict[supplier_id]
        download_filename = generate_download_filename(supplier_id, document_name, supplier_name)

    # Do the actual upload
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
    if not tsv_path or not tsv_path.endswith('.tsv'):
        return None
    suppliers_name_dict = {}
    with open(tsv_path, 'r') as tsvfile:
        tsv_reader = csv.reader(tsvfile, delimiter='\t')
        for row in tsv_reader:
            suppliers_name_dict[row[0]] = row[1]
    return suppliers_name_dict
