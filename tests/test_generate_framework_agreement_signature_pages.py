
import pytest

from unittest import mock

from dmtestutils.api_model_stubs import (
    DraftServiceStub,
    FrameworkStub,
    SupplierFrameworkStub,
    SupplierStub,
)

import dmscripts.generate_framework_agreement_signature_pages as generate_framework_agreement_signature_pages


@pytest.fixture
def suppliers():
    return {
        1001: {
            "onFramework": True,
            "drafts": [
                {
                    "status": "submitted",
                },
            ],
        },
        2003: {
            "onFramework": True,
            "drafts": [
                {
                    "status": "not-submitted",
                },
            ],
        },
        3004: {
            "onFramework": False,
        },
    }


@pytest.fixture()
def framework():
    return FrameworkStub().response()


@pytest.fixture()
def api(suppliers):
    with mock.patch("dmapiclient.DataAPIClient") as api_mock:
        api_mock.get_interested_suppliers.return_value = {"interestedSuppliers": [id for id in suppliers]}
        api_mock.get_supplier.side_effect = \
            lambda id: SupplierStub(id=id).single_result_response()
        api_mock.get_supplier_framework_info.side_effect = \
            lambda id, slug: (
                SupplierFrameworkStub(
                    supplier_id=id,
                    framework_slug=slug,
                    on_framework=suppliers[id]["onFramework"],
                    with_declaration=True,
                    declaration_status="complete",
                ).single_result_response()
            )
        api_mock.find_draft_services_iter.side_effect = \
            lambda id, framework: [
                DraftServiceStub(
                    supplier_id=id,
                    framework_slug=framework,
                    status=draft["status"],
                ).response()
                for draft in suppliers[id].get("drafts", [])
            ]
        yield api_mock


def test_finds_all_suppliers_on_framework_and_with_at_least_one_completed_draft_service(api, framework):
    suppliers = generate_framework_agreement_signature_pages.find_suppliers(api, framework)
    suppliers = list(suppliers)
    assert len(suppliers) == 1
