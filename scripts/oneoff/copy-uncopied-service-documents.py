#!/usr/bin/env python3

import sys
from urllib.parse import urljoin

from dmapiclient import DataAPIClient
from dmutils.env_helpers import (
    get_api_endpoint_from_stage,
    get_assets_endpoint_from_stage,
)
from dmutils.s3 import S3

sys.path.insert(0, ".")

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.logging_helpers import configure_logger
from dmscripts.helpers.updated_by_helpers import get_user
from dmscripts.publish_draft_services import (
    _parse_document_url,
    _get_live_document_path,
    _copy_document,
    _get_draft_document_path,
)

if __name__ == "__main__":
    logger = configure_logger()

    STAGE = "production"
    FRAMEWORK = "g-cloud-12"
    DRAFT_BUCKET = S3("digitalmarketplace-submissions-production-production")
    DOCUMENTS_BUCKET = S3("digitalmarketplace-documents-production-production")

    data = DataAPIClient(
        get_api_endpoint_from_stage(STAGE), get_auth_token("api", STAGE), user=get_user(),
    )

    live_assets_endpoint = get_assets_endpoint_from_stage(STAGE)

    for service in data.find_services_iter(
        framework=FRAMEWORK,
        status="published",
    ):
        service_id = service["id"]
        for key, value in service.items():
            if (
                isinstance(value, str)
                and "submissions" in value
                and value.endswith("pdf")
            ):
                logger.info(f"{service_id}: {key} {value}")

                parsed_document_url = _parse_document_url(value, FRAMEWORK)
                draft_document_path = _get_draft_document_path(
                    parsed_document_url, FRAMEWORK
                )
                live_document_path = _get_live_document_path(
                    parsed_document_url, FRAMEWORK, service_id
                )

                try:
                    _copy_document(
                        DRAFT_BUCKET,
                        DOCUMENTS_BUCKET,
                        draft_document_path,
                        live_document_path,
                        dry_run=False,
                    )
                except ValueError as e:
                    if not str(e).startswith("Target key already exists in S3"):
                        raise e

                data.update_service(
                    service_id, {key: urljoin(live_assets_endpoint, live_document_path)}
                )
