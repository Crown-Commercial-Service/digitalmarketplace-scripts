#!/usr/bin/env python

import argparse
import sys

sys.path.insert(0, '.')
from dmapiclient import DataAPIClient
from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage

from typing import List


def get_affected_drafts_services(api_client: DataAPIClient) -> List[dict]:
    all_drafts = api_client.find_draft_services_by_framework('digital-outcomes-and-specialists-5')["services"]

    return [draft for draft in all_drafts if draft_service_contains_dos4_answer(draft)]


def draft_service_contains_dos4_answer(draft: dict) -> bool:
    invalid_answers = {
        "agileCoachPriceMin",
        "businessAnalystPriceMin",
        "communicationsManagerPriceMin",
        "contentDesignerPriceMin",
        "dataArchitectPriceMin",
        "dataEngineerPriceMin",
        "dataScientistPriceMin",
        "deliveryManagerPriceMin",
        "designerPriceMin",
        "developerPriceMin",
        "performanceAnalystPriceMin",
        "portfolioManagerPriceMin",
        "productManagerPriceMin",
        "programmeManagerPriceMin",
        "qualityAssurancePriceMin",
        "securityConsultantPriceMin",
        "serviceManagerPriceMin",
        "technicalArchitectPriceMin",
        "userResearcherPriceMin",
        "webOperationsPriceMin",
        "developerAccessibleApplications",
        "contentDesignerAccessibleApplications",
        "qualityAssuranceAccessibleApplications",
        "technicalArchitectAccessibleApplications",
        "webOperationsAccessibleApplications",
        "serviceManagerAccessibleApplications",
        "designerAccessibleApplications"
    }

    return len(invalid_answers.union(set(draft["services"].keys()))) > 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("stage", type=str)

    args = parser.parse_args()

    data = DataAPIClient(
        get_api_endpoint_from_stage(args.stage),
        get_auth_token('api', args.stage)
    )

    affected_drafts = get_affected_drafts_services(data)
    print(affected_drafts)
