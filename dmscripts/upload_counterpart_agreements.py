import getpass

from dmutils.documents import generate_timestamped_document_upload_path, generate_download_filename, \
    COUNTERPART_FILENAME

from dmscripts.bulk_upload_documents import get_supplier_id_from_framework_file_path


def upload_counterpart_file(bucket, framework_slug, file_path, dry_run, client, logger):
    supplier_id = get_supplier_id_from_framework_file_path(file_path)
    supplier_framework = client.get_supplier_framework_info(supplier_id, framework_slug)
    supplier_framework = supplier_framework['frameworkInterest']
    supplier_name = supplier_framework['declaration']['nameOfOrganisation']
    download_filename = generate_download_filename(supplier_id, COUNTERPART_FILENAME, supplier_name)

    upload_path = generate_timestamped_document_upload_path(
        framework_slug,
        supplier_id,
        "agreements",
        COUNTERPART_FILENAME
    )
    try:
        if not dry_run:
            # Upload file
            with open(file_path) as file_contents:
                bucket.save(upload_path, file_contents, acl='private', move_prefix=None,
                            download_filename=download_filename)
                logger.info("UPLOADED: '{}' to '{}'".format(file_path, upload_path))

            # Save filepath to framework agreement
            client.update_framework_agreement(
                supplier_framework['agreementId'],
                {"countersignedAgreementPath": upload_path},
                'upload-counterpart-agreements script run by {}'.format(getpass.getuser())
            )
            logger.info("countersignedAgreementPath='{}' for agreement ID {}".format(
                upload_path, supplier_framework['agreementId'])
            )
        else:
            logger.info("[Dry-run] UPLOAD: '{}' to '{}'".format(file_path, upload_path))
            logger.info("[Dry-run] countersignedAgreementPath='{}' for agreement ID {}".format(
                upload_path, supplier_framework['agreementId'])
            )

    except Exception as e:
        logger.info("ERROR {}".format(e.message))
