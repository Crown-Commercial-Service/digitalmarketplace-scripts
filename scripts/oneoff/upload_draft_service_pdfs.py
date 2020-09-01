#!/usr/bin/env python
"""
Experimental script to provide an alternative method of manually uploading documents for draft services,
for example if a user has accessibility issues that prevent them using the site, they could submit documents
to CCS via email.

IMPORTANT: ensure you have the correct AWS_PROFILE env variable set for the environment, otherwise the S3 uploads will
fail.

- For each file in the given folder
- Look up draft service ID by supplier ID and service name
- Determine whether doc is pricing/SFIA/T&C/service definition
- Upload documents to S3, following the standardised naming scheme <draft_id>-<doctype>-<datestamp>.pdf
- Update draft service with S3 URLs

Any failures will skip and continue to the next document in the folder.

Not included: Modern Slavery Statement documents

Usage: upload_draft_service_pdfs <framework> <stage> [options]

Options:
    --folder=<folder>                                     Folder to bulk-upload files
    --file-format                                         File format to check for (default: pdf)
    --dry-run                                             List actions that would have been taken
    -h, --help                                            Show this screen

"""
import sys
import os
import urllib.parse as urlparse
from dmapiclient.data import DataAPIClient

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.file_helpers import get_all_files_of_type
from dmscripts.helpers.s3_helpers import get_bucket_name
from scripts.oneoff.update_draft_service_via_csv import find_draft_id_by_service_name

from dmutils.env_helpers import get_api_endpoint_from_stage, get_assets_endpoint_from_stage
from dmutils.documents import default_file_suffix, generate_download_filename
from dmutils.s3 import S3

from docopt import docopt


DOC_TYPES = {
    'servicedefinitiondocument': 'serviceDefinitionDocumentURL',
    'termsandconditions': 'termsAndConditionsDocumentURL',
    'sfiaratecard': 'sfiaRateDocumentURL',
    'pricingdocument': 'pricingDocumentURL'
}


def _normalise_service_name(name, file_format):
    return name.lower().\
        replace('-', '').\
        replace('_', ''). \
        replace(':', ''). \
        replace(' ', '').\
        replace(f'.{file_format}', '')


def get_info_from_filename(filepath, client, framework_slug, file_format):
    supplier_id, doc_type, draft_id = None, None, None

    # Split out Supplier ID first - should be the prefix
    supplier_id, service_name_and_doctype = filepath.split('-', maxsplit=1)
    service_name = _normalise_service_name(service_name_and_doctype, file_format)

    for dt in DOC_TYPES.keys():
        if dt in service_name:
            doc_type = dt

    if doc_type is None:
        # Can't continue
        return int(supplier_id), None, None

    service_name = service_name.replace(doc_type, '')
    draft_id = find_draft_id_by_service_name(client, supplier_id, service_name, framework_slug)
    if draft_id == 'multi':
        print("Multiple drafts found for service name", service_name)
        return int(supplier_id), doc_type, None
    elif draft_id is None:
        print("No draft found for service name", service_name)
        return int(supplier_id), doc_type, None

    return int(supplier_id), doc_type, draft_id


def construct_upload_filename(draft_id, doc_type, file_format):
    datestamp = default_file_suffix()
    return f"{draft_id}-{doc_type}-{datestamp}.{file_format}"


def upload_to_submissions_bucket(
    document_name, bucket, bucket_category, framework_slug, supplier_id, file_path, dry_run, supplier_name_dict
):
    # Construct the upload path
    upload_path = '{0}/{1}/{2}/{3}'.format(framework_slug, bucket_category, supplier_id, document_name)

    # Download filename, if available
    if supplier_name_dict is None:
        download_filename = None
    else:
        supplier_name = supplier_name_dict[supplier_id]
        download_filename = generate_download_filename(supplier_id, document_name, supplier_name)
        print(download_filename)

    # Do the actual upload
    if not dry_run:
        with open(file_path, 'rb') as source_file:
            # TODO check if we need download_filename for submissions
            bucket.save(upload_path, source_file, acl='bucket-owner-full-control', download_filename=download_filename)
            print(f"Successfully uploaded {upload_path} to S3")

    else:
        print("[Dry-run] UPLOAD: '{}' to '{}'".format(file_path, upload_path))


def update_draft_service_with_document_paths(full_document_url, doc_type, draft_id, api_client, dry_run):
    draft_json = {
        DOC_TYPES[doc_type]: full_document_url
    }
    if dry_run:
        # Log something
        print(f"[Dry-run] API: Would update draft ID {draft_id} with some JSON:")
        print(draft_json)
        return True

    try:
        api_client.update_draft_service(
            draft_id,
            draft_json,
            'one off PDF upload script'
        )
        print(f"Draft ID {draft_id} updated.")
        draft = api_client.get_draft_service(draft_id)
        if draft['validationErrors']:
            print(f"Validation errors:")
            print(draft['validationErrors'])
            return False
        else:
            print("Ready to be marked as complete.")
            return True
    except Exception as exc:
        print(str(exc))
    return False


def output_results(unidentifiable_files, successful_draft_ids, failed_draft_ids):
    # Output successful / failed draft IDs
    if successful_draft_ids:
        with open('successful-uploads-draft-ids.txt', 'w') as f:
            for d in successful_draft_ids:
                f.write(str(d) + '\n')

    if failed_draft_ids:
        with open('failed-uploads-draft-ids.txt', 'w') as f:
            for d in failed_draft_ids:
                f.write(str(d) + '\n')

    if unidentifiable_files:
        with open('unidentifiable-draft-service-files.txt', 'w') as f:
            for d in unidentifiable_files:
                f.write(str(d) + '\n')


def upload_draft_service_pdfs_from_folder(
    bucket, bucket_category, assets_path, local_directory, api_client, framework_slug, file_format, dry_run
):
    failed_draft_ids = []
    successful_draft_ids = []
    unidentifiable_files = []

    # Parse files in folder
    for path in get_all_files_of_type(local_directory, file_format):
        # Check file is open document format or PDF
        file_name = os.path.basename(path)
        print(f"File name: {file_name}")
        _, file_extension = os.path.splitext(file_name)
        if file_extension not in [".pdf", ".odt", ".ods", ".odp"]:
            print(f'Invalid file type {file_extension}, skipping')
            unidentifiable_files.append(file_name)
            continue

        # Get IDs etc
        supplier_id, doc_type, draft_id = get_info_from_filename(file_name, api_client, framework_slug, file_format)
        if supplier_id is None:
            print("Unable to determine Supplier ID")
            unidentifiable_files.append(file_name)
            continue
        if doc_type is None:
            print("Unable to determine doctype")
            unidentifiable_files.append(file_name)
            continue
        if draft_id is None:
            print("Unable to determine Draft ID")
            unidentifiable_files.append(file_name)
            continue
        print(f"Found Supplier ID {supplier_id}, file type {doc_type} and Draft ID {draft_id}")

        # Get supplier name, to add to S3 metadata (ie visible to buyers on download)
        supplier = api_client.get_supplier(supplier_id)
        supplier_name_dict = {supplier_id: supplier['suppliers']['name']}
        new_filename = construct_upload_filename(draft_id, doc_type, file_format)

        # Upload to S3
        upload_to_submissions_bucket(
            new_filename, bucket, bucket_category, framework_slug, supplier_id, path, dry_run, supplier_name_dict
        )

        # Try updating service data
        full_url = urlparse.urljoin(
            assets_path,
            f"suppliers/assets/{framework_slug}/submissions/{supplier_id}/{new_filename}"
        )
        if update_draft_service_with_document_paths(full_url, doc_type, draft_id, api_client, dry_run):
            successful_draft_ids.append(draft_id)
        else:
            failed_draft_ids.append(draft_id)

    output_results(unidentifiable_files, successful_draft_ids, failed_draft_ids)


if __name__ == "__main__":
    arguments = docopt(__doc__)

    # Get script arguments
    framework_slug = arguments['<framework>']
    stage = arguments['<stage>'] or 'local'
    dry_run = arguments['--dry-run'] or None

    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token('api', stage)
    )
    local_directory = arguments['--folder']
    file_format = arguments.get('--file-format', 'pdf')

    # Check framework status
    framework = data_api_client.get_framework(framework_slug)
    framework_status = framework['frameworks']['status']
    if framework_status not in ['open']:
        print(f"Cannot update services for framework {framework_slug} in status '{framework_status}'")
        exit(1)

    # Check folder exists
    if local_directory and not os.path.exists(local_directory):
        print(f"Local directory {local_directory} not found. Aborting upload.")
        exit(1)

    # Setup S3 stuff
    bucket_category = "submissions"
    bucket = None if dry_run else S3(get_bucket_name(stage, bucket_category))
    try:
        assets_path = get_assets_endpoint_from_stage(stage)
    except NotImplementedError:
        assets_path = "http://localhost"

    upload_draft_service_pdfs_from_folder(
        bucket,
        bucket_category,
        assets_path,
        local_directory,
        data_api_client,
        framework_slug,
        file_format,
        dry_run
    )
