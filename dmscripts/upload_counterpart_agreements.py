import getpass
from itertools import chain

from dmutils.s3 import S3ResponseError
from dmapiclient import APIError
from dmutils.documents import generate_timestamped_document_upload_path, generate_download_filename, \
    COUNTERPART_FILENAME
from dmutils.email.exceptions import EmailError

from dmscripts.bulk_upload_documents import get_supplier_id_from_framework_file_path
from dmscripts.helpers import logging_helpers


def upload_counterpart_file(
    bucket,
    framework,
    file_path,
    dry_run,
    data_api_client,
    dm_notify_client=None,
    notify_template_id=None,
    notify_fail_early=True,
    logger=None,
):
    if bool(dm_notify_client) != bool(notify_template_id):
        raise TypeError("Either specify both dm_notify_client and notify_template_id or neither")

    logger = logger or logging_helpers.getLogger()

    supplier_id = get_supplier_id_from_framework_file_path(file_path)
    supplier_framework = data_api_client.get_supplier_framework_info(supplier_id, framework["slug"])
    supplier_framework = supplier_framework['frameworkInterest']
    supplier_name = supplier_framework['declaration']['supplierRegisteredName']
    download_filename = generate_download_filename(supplier_id, COUNTERPART_FILENAME, supplier_name)

    email_addresses_to_notify = dm_notify_client and frozenset(chain(
        (supplier_framework["declaration"]["primaryContactEmail"],),
        (
            user["emailAddress"]
            for user in data_api_client.find_users_iter(supplier_id=int(supplier_id)) if user["active"]
        ),
    ))

    upload_path = generate_timestamped_document_upload_path(
        framework["slug"],
        supplier_id,
        "agreements",
        COUNTERPART_FILENAME
    )
    try:
        if not dry_run:
            # Upload file
            with open(file_path) as source_file:
                bucket.save(upload_path, source_file, acl='bucket-owner-full-control',
                            download_filename=download_filename)
                logger.info("UPLOADED: '{}' to '{}'".format(file_path, upload_path))

            # Save filepath to framework agreement
            data_api_client.update_framework_agreement(
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

        failed_send_email_calls = 0
        for notify_email in (email_addresses_to_notify or ()):
            try:
                if not dry_run:
                    dm_notify_client.send_email(notify_email, notify_template_id, {
                        "framework_slug": framework["slug"],
                        "framework_name": framework["name"],
                        "supplier_name": supplier_name,
                    }, allow_resend=True)
                else:
                    logger.info("[Dry-run] Send notify email to %s", notify_email)
            except EmailError as e:
                if notify_fail_early:
                    raise
                else:
                    failed_send_email_calls += 1
    # just catching these exceptions for logging then reraising
    except (OSError, IOError) as e:
        logger.error("Error reading file '{}': {}".format(file_path, e.message))
        raise
    except S3ResponseError as e:
        logger.error("Error uploading '{}' to '{}': {}".format(file_path, upload_path, e.message))
        raise
    except APIError as e:
        logger.error("API error setting upload path '{}' on agreement ID {}: {}".format(
            upload_path,
            supplier_framework['agreementId'],
            e.message)
        )
        raise

    if failed_send_email_calls:
        raise EmailError("{} notify send_emails calls failed".format(failed_send_email_calls))
