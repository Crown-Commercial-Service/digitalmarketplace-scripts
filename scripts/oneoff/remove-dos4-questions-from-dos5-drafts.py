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

    return len(invalid_answers.union(set(draft.keys()))) > 0 and draft['status'] == 'not-submitted'


def remove_dos4_answers(api_client: DataAPIClient, draft: dict, developer_email: str) -> dict:
    return api_client.update_draft_service(
        draft['id'],
        {
            "agileCoachPriceMin": None,
            "businessAnalystPriceMin": None,
            "communicationsManagerPriceMin": None,
            "contentDesignerPriceMin": None,
            "dataArchitectPriceMin": None,
            "dataEngineerPriceMin": None,
            "dataScientistPriceMin": None,
            "deliveryManagerPriceMin": None,
            "designerPriceMin": None,
            "developerPriceMin": None,
            "performanceAnalystPriceMin": None,
            "portfolioManagerPriceMin": None,
            "productManagerPriceMin": None,
            "programmeManagerPriceMin": None,
            "qualityAssurancePriceMin": None,
            "securityConsultantPriceMin": None,
            "serviceManagerPriceMin": None,
            "technicalArchitectPriceMin": None,
            "userResearcherPriceMin": None,
            "webOperationsPriceMin": None,
            "developerAccessibleApplications": None,
            "contentDesignerAccessibleApplications": None,
            "qualityAssuranceAccessibleApplications": None,
            "technicalArchitectAccessibleApplications": None,
            "webOperationsAccessibleApplications": None,
            "serviceManagerAccessibleApplications": None,
            "designerAccessibleApplications": None
        },
        developer_email
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("stage", type=str)
    parser.add_argument("developer_email", type=str)

    args = parser.parse_args()

    data = DataAPIClient(
        get_api_endpoint_from_stage(args.stage),
        get_auth_token('api', args.stage)
    )
    
    updated_drafts = [
        remove_dos4_answers(data, draft, args.developer_email) for draft
        in get_affected_drafts_services(data)
    ]
    
    for draft in updated_drafts:
        print(f"Supplier id: {draft['supplierId']}")
        print(f"Draft id: {draft['id']}")
