#!/usr/bin/env python3
"""
PREREQUISITE: For document migration to work you'll need AWS credentials set up for the relevant environment:
              Save your aws_access_key_id and aws_secret_access_key in ~/.aws/credentials
              If you have more than one set of credentials in there then be sure to set your AWS_PROFILE environment
              variable to reference the right credentials before running the script.
              THIS SCRIPT NEEDS TO BE RUN BY AN AWS IAM ENTITY FROM THE SAME ACCOUNT AS THE DOCUMENTS BUCKET BEING
              UPLOADED TO. THIS IS SO THE S3 OBJECT OWNER IS THAT ACCOUNT AND NOT A DIFFERENT ACCOUNT. OTHERWISE THERE
              WILL BE PERMISSION ISSUES IF A SUPPLIER UPDATES THEIR DOCUMENTS. CHANGING OBJECT OWNERS ONCE UPLOADED
              IS NOT IMPOSSIBLE BUT IT IS A RIGHT FAFF. CURRENTLY THERE IS NOT AN EASY WAY TO DO THIS FROM JENKINS. A
              PROCESS COULD BE SET UP TO ALLOW JENKINS TO ASSUME A DIFFERENT ROLE.

For a G-Cloud style framework (with uploaded documents to migrate) this will:
 1. Find all suppliers awarded onto the framework
 2. Find all their submitted draft services on the framework
 3. Migrate these from drafts to "real" services, which includes moving documents to the live documents bucket
    and updating document URLs in the migrated version of the services
Usage:
    scripts/publish-draft-services.py <framework_slug> <stage> [<draft_bucket>]
        [<documents_bucket>] [--dry-run] [--skip-docs-if-published] [--draft-ids=<filename>]

If you specify the `--draft-ids` parameter, pass in list of newline-separated draft ids. This script will then do a
full re-publish of just those drafts (i.e. try to re-publish it, and then copy the documents across again and update
those links).
"""
from functools import partial
import sys

sys.path.insert(0, '.')

from docopt import docopt

import dmapiclient
from dmutils.s3 import S3
from dmutils.env_helpers import get_api_endpoint_from_stage, get_assets_endpoint_from_stage

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.logging_helpers import configure_logger
from dmscripts.publish_draft_services import publish_draft_services, copy_draft_documents

_document_keys_by_framework_family = {
    "g-cloud": (
        'pricingDocumentURL',
        'serviceDefinitionDocumentURL',
        'sfiaRateDocumentURL',
        'termsAndConditionsDocumentURL',
    ),
    "digital-outcomes-and-specialists": (),
}

_expected_framework_statuses = ("pending", "standstill",)


if __name__ == '__main__':
    arguments = docopt(__doc__)

    configure_logger()

    STAGE = arguments['<stage>']
    api_url = get_api_endpoint_from_stage(STAGE)

    client = dmapiclient.DataAPIClient(api_url, get_auth_token('api', STAGE))
    DRAFT_BUCKET = arguments.get('<draft_bucket>') and S3(arguments['<draft_bucket>'])
    DOCUMENTS_BUCKET = arguments.get('<documents_bucket>') and S3(arguments['<documents_bucket>'])
    DRY_RUN = arguments['--dry-run']
    FRAMEWORK_SLUG = arguments['<framework_slug>']
    DRAFT_IDS_FILE = arguments.get('--draft-ids') and open(arguments['--draft-ids'], "r")
    SKIP_DOCS_IF_PUBLISHED = arguments['--skip-docs-if-published']

    framework = client.get_framework(FRAMEWORK_SLUG)["frameworks"]
    if framework["status"] not in _expected_framework_statuses:
        raise ValueError(
            f"Framework status expected to be one of {_expected_framework_statuses}, not {framework['status']!r}"
        )

    document_keys = _document_keys_by_framework_family.get(framework["family"])

    if document_keys and not (DRAFT_BUCKET and DOCUMENTS_BUCKET):
        raise ValueError(
            f"Must supply both <draft_bucket> and <documents_bucket> arguments for framework {FRAMEWORK_SLUG!r}"
        )

    copy_documents_callable = document_keys and partial(
        copy_draft_documents,
        DRAFT_BUCKET,
        DOCUMENTS_BUCKET,
        document_keys,
        "https://dummy.endpoint" or get_assets_endpoint_from_stage(STAGE),
    )

    publish_draft_services(
        client,
        FRAMEWORK_SLUG,
        copy_documents_callable,
        DRAFT_IDS_FILE,
        DRY_RUN,
        SKIP_DOCS_IF_PUBLISHED,
    )
