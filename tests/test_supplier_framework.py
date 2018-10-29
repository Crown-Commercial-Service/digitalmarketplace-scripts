from .assessment_helpers import BaseAssessmentTest
from dmscripts.supplier_framework import SupplierFrameworkMethods
from mock import create_autospec
from dmapiclient import DataAPIClient
import json


class TestSupplierFramework(BaseAssessmentTest):

    def _supplier_framework_response(self):
        with open("tests/fixtures/test_supplier_frameworks_response.json", 'r') as response_file:
            return json.load(response_file)['supplierFrameworks']

    def test_suppliers_application_failed_to_framework(self):
        mocked_api_client = create_autospec(DataAPIClient)
        mocked_api_client.find_framework_suppliers_iter.side_effect = lambda *args, **kwargs: \
            iter(self._supplier_framework_response())
        supplier_framework = SupplierFrameworkMethods(mocked_api_client, 'g-cloud-8')
        assert supplier_framework.suppliers_application_failed_to_framework() == [12345, 23456]
