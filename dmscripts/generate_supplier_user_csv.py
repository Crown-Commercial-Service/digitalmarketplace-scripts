import csv
from dmutils.s3 import S3ResponseError
from dmapiclient.errors import HTTPError

from dmscripts.models.writecsv import csv_path


def generate_supplier_csv(framework_slug, data_api_client, logger):
    framework = data_api_client.get_framework(framework_slug).get("frameworks")

    try:
        supplier_rows = data_api_client.export_suppliers(framework_slug).get("suppliers", [])
    except HTTPError as e:
        if e.response.status_code == 400:
            logger.warn(f"Framework '{framework_slug}' is not open, no supplier data is available")
            supplier_rows = []
        else:
            raise
    else:
        if not supplier_rows:
            logger.warn(f"No supplier data found for framework {framework_slug}")

    supplier_and_framework_headers = [
        "supplier_id",
        "supplier_name",
        "supplier_organisation_size",
        "duns_number",
        "companies_house_number",
        "other_company_registration_number",
        "registered_name",
        "declaration_status",
        "application_status",
        "application_result",
        "framework_agreement",
        "variations_agreed",
    ]
    service_count_headers = [lot['slug'] for lot in framework['lots']]
    contact_info_headers = [
        'contact_name',
        'contact_email',
        'contact_phone_number',
        'address_first_line',
        'address_city',
        'address_postcode',
        'address_country',
    ]

    filename = "official-details-for-suppliers-{}".format(framework_slug)

    supplier_headers = supplier_and_framework_headers + ["total_number_of_services"] + \
        ["service-count-{}".format(h) for h in service_count_headers] + contact_info_headers

    formatted_rows = []
    for row in supplier_rows:
        # Include an extra column with the total number of services across all lots
        service_counts = [row['published_services_count'][heading] for heading in service_count_headers]
        total_number_of_services = sum(service_counts)

        formatted_rows.append(
            [row[heading] for heading in supplier_and_framework_headers] +
            [total_number_of_services] +
            service_counts +
            [row['contact_information'][heading] for heading in contact_info_headers]
        )

    return supplier_headers, formatted_rows, filename


def generate_user_csv(framework_slug, data_api_client, user_research_opted_in, logger):
    """
    Call API endpoint
    Get CSV headers and rows
    """
    user_headers = [
        "email address",
        "user_name",
        "supplier_id",
        "declaration_status",
        "application_status",
        "application_result",
        "framework_agreement",
        "variations_agreed",
        "published_service_count"
    ]

    user_rows = []
    try:
        user_rows = data_api_client.export_users(framework_slug).get("users", [])
    except HTTPError as e:
        if e.response.status_code == 400:
            logger.warn(f"Framework '{framework_slug}' is not open, no user data is available")
        else:
            raise
    else:
        if not user_rows:
            logger.warn(f"No user data found for framework {framework_slug}")

    if user_research_opted_in:
        filename = "user-research-suppliers-on-{}".format(framework_slug)
    else:
        filename = "all-email-accounts-for-suppliers-{}".format(framework_slug)

    formatted_rows = []
    for row in user_rows:
        if user_research_opted_in:
            if row['user_research_opted_in']:
                formatted_rows.append([row[heading] for heading in user_headers])
        else:
            formatted_rows.append([row[heading] for heading in user_headers])

    return user_headers, formatted_rows, filename


def upload_to_s3(file_path, framework_slug, download_filename, bucket, dry_run, logger):
    # e.g. in the 'digitalmarketplace-reports-preview-preview' bucket, the
    # path would be 'g-cloud-10/official-details-for-suppliers-g-cloud-10.csv'

    try:
        if dry_run:
            logger.info("[Dry-run] UPLOAD: '{}' to '{}'".format(file_path, download_filename))
        else:
            # Upload file - need to open in binary mode as it's not plain text
            with open(file_path, 'rb') as source_file:
                # S3 bucket already logging external request
                bucket.save(
                    "{}/reports/{}".format(framework_slug, download_filename),
                    source_file,
                    acl='bucket-owner-full-control',
                    download_filename=download_filename
                )
                logger.info("UPLOADED: '{}' to '{}'".format(file_path, download_filename))

    # Catch and re-raise these exceptions for logging
    except (OSError, IOError) as e:
        logger.error("Error reading file '{}': {}".format(file_path, e.message))
        raise
    except S3ResponseError as e:
        logger.error("Error uploading '{}' to '{}': {}".format(file_path, download_filename, str(e)))
        raise


def _build_csv(file_path, headers, rows):
    with open(file_path, 'w') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"')
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)


def generate_csv_and_upload_to_s3(
    bucket, framework_slug, report_type, output_dir, data_api_client,
    dry_run=False, user_research_opted_in=False, logger=None
):
    # Fetch data from API
    if report_type == 'users':
        headers, rows, download_filename = generate_user_csv(
            framework_slug, data_api_client, user_research_opted_in=user_research_opted_in, logger=logger
        )

    else:
        headers, rows, download_filename = generate_supplier_csv(framework_slug, data_api_client, logger=logger)

    # no need to create an empty csv
    if not rows:
        return True

    # Save CSV to output dir and upload to S3
    file_path = csv_path(output_dir, download_filename)
    _build_csv(file_path, headers, rows)
    upload_to_s3(file_path, framework_slug, "{}.csv".format(download_filename), bucket, dry_run=dry_run, logger=logger)

    return True
