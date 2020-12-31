#!/usr/bin/env python3

"""
PREREQUISITE: You'll need AWS credentials set up for the environment that you're uploading to:
              Save your aws_access_key_id and aws_secret_access_key in ~/.aws/credentials
              If you have more than one set of credentials in there then be sure to set your AWS_PROFILE environment
              variable to reference the right credentials before running the script.
              Alternatively, if this script is being run from Jenkins, do not provide any credentials and boto will use
              the Jenkins IAM role. It should have the required permissions for the buckets.

This will:
 * scan a directory for pdf files (they should be in the format <supplier_id>-some-ignored-words.pdf but this isn't
   enforced)
   and for each file:

   * get the SupplierFramework object for the supplier

   * upload them to the S3 documents bucket for <stage> with the file path:
     <framework_slug>/agreements/<supplier_id>/<supplier_id>-counterpart-signature-page.pdf
     e.g.
     g-cloud-8/agreements/1234/1234-counterpart-signature-page.pdf

   * set a "download filename" that the file will be downloaded as, which is:
     <supplier-name>-<supplier-id>-<document-name>.<document-type>
     where supplier_name is the sanitised version of the name from their supplier declaration for the framework

   * set the "countersigned agreement path" in the current FrameworkAgreement referenced by the SupplierFramework

   * if <notify_key> and <notify_template_id> are provided, will send a notification email to all the supplier's active
     users (and their primaryContactEmail for that framework)

Usage: scripts/upload-counterpart-agreements.py <stage> <documents_directory> <framework_slug> <content_path> [options]

Options:
    --dry-run                                   # Don't actually do anything
    --notify-key=<notify_key>                   # GOV.UK Notify service key
    --notify-template-id=<notify_template_id>   # GOV.UK Notify template id for notification email

"""

import sys
sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.file_helpers import get_all_files_of_type
from dmscripts.upload_counterpart_agreements import upload_counterpart_file
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging
from dmscripts.helpers.s3_helpers import get_bucket_name
from dmutils.env_helpers import get_api_endpoint_from_stage
from dmcontent.content_loader import ContentLoader

from docopt import docopt
from dmapiclient import DataAPIClient, APIError

from dmutils.s3 import S3, S3ResponseError
from dmutils.email.exceptions import EmailError

from dmscripts.helpers.email_helpers import scripts_notify_client


logger = logging_helpers.configure_logger({
    'dmapiclient.base': logging.WARNING,
    'notifications_python_client.base': logging.WARNING,
})


if __name__ == '__main__':
    arguments = docopt(__doc__)

    if bool(arguments.get("--notify-key")) != bool(arguments.get("--notify-template-id")):
        raise ValueError("Either specify both --notify-key and --notify-template-id or neither")

    stage = arguments['<stage>']
    data_api_client = DataAPIClient(get_api_endpoint_from_stage(stage), get_auth_token('api', stage))
    framework_slug = arguments['<framework_slug>']
    framework = data_api_client.get_framework(framework_slug)["frameworks"]
    document_directory = arguments['<documents_directory>']
    content_path = arguments['<content_path>']
    content_loader = ContentLoader(content_path)
    content_loader.load_messages(framework_slug, ['e-signature'])
    contract_title = content_loader.get_message(framework_slug, 'e-signature', 'framework_contract_title')

    dry_run = arguments['--dry-run']
    dm_notify_client = arguments.get("--notify-key") and scripts_notify_client(arguments["--notify-key"], logger=logger)

    if dry_run:
        bucket = None
    else:
        bucket = S3(get_bucket_name(stage, "agreements"))

    failure_count = 0

    for file_path in get_all_files_of_type(document_directory, "pdf"):
        try:
            upload_counterpart_file(
                bucket,
                framework,
                file_path,
                dry_run,
                data_api_client,
                contract_title,
                dm_notify_client=dm_notify_client,
                notify_template_id=arguments.get("--notify-template-id"),
                notify_fail_early=False,
                logger=logger,
            )
        except (OSError, IOError, S3ResponseError, EmailError, APIError):
            # upload_counterpart_file should have already logged these so no need here
            failure_count += 1

    # we return the failure_count as the error code, though note these count "failures" quite pessimistically, a single
    # email's notify call failing will count the supplier's action as a failure even if the file was successfully
    # uploaded (and possibly even other emails managed to get out)
    sys.exit(failure_count)
