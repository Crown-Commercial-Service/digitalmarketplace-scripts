import pytest

from itertools import product, repeat

from dmscripts.mark_definite_framework_results import mark_definite_framework_results

from .assessment_helpers import BaseAssessmentTest, BaseAssessmentMismatchedOnFrameworksTestMixin


def _assert_draft_service_result_actions(client, expected_draft_services_actions, dry_run=False):
    update_draft_service_status_calls = [call[0] for call in client.update_draft_service_status.call_args_list]

    expected_calls = [] if dry_run else [
        (supplier_id, "submitted" if submitted else "failed", "Blazes Boylan")
        for supplier_id, submitted
        in expected_draft_services_actions
    ]
    assert update_draft_service_status_calls == expected_calls


def _assert_set_framework_result_actions(client, expected_set_framework_actions, dry_run=False):
    set_framework_result_calls = [call[0] for call in client.set_framework_result.call_args_list]

    expected_calls = [] if dry_run else [
        (supplier_id, "h-cloud-99", result, "Blazes Boylan") for supplier_id, result in expected_set_framework_actions
    ]
    assert set_framework_result_calls == expected_calls


class TestNoPrevResults(BaseAssessmentTest):
    def _get_supplier_frameworks(self):
        # no onFramework values should be set yet
        return {
            k: dict(v, onFramework=None) for k, v in super(TestNoPrevResults, self)._get_supplier_frameworks().items()
        }

    def _get_draft_services(self):
        # no draft services should have been failed yet
        return {
            k: tuple(
                dict(s, status=("submitted" if s["status"] == "failed" else s["status"])) for s in v
            ) for k, v in super(TestNoPrevResults, self)._get_draft_services().items()
        }

    @pytest.mark.parametrize(
        # we can very easily parametrize this into the 16 possible combinations of these flags - the results for the
        # first three flags should be identical and it's very easy to flip some of the assertions for the dry_run mode
        "reassess_passed_suppliers,reassess_failed_suppliers,reassess_failed_suppliers_draft_services,dry_run",
        tuple(product(*repeat((False, True,), 4))),
    )
    def test_with_draft_services_schema(
            self,
            reassess_passed_suppliers,
            reassess_failed_suppliers,
            reassess_failed_suppliers_draft_services,
            dry_run,
    ):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_discretionary_pass_schema=self._declaration_definite_pass_schema()["definitions"]["baseline"],
            service_schema=self._draft_service_schema(),
            dry_run=dry_run,
            reassess_passed_suppliers=reassess_passed_suppliers,
            reassess_failed_suppliers=reassess_failed_suppliers,
            reassess_failed_draft_services=reassess_failed_suppliers_draft_services,
        )

        expected_set_framework_actions = (
            (2345, False),
            (3456, False),
            (4321, True),
            (4567, False),
            (5432, False),
            (6543, True),
            (8765, True),
        )
        expected_draft_services_actions = (
            (999003, False),
            (999005, False),
            (999012, False),
        )
        _assert_draft_service_result_actions(self.mock_data_client, expected_draft_services_actions, dry_run=dry_run)
        _assert_set_framework_result_actions(self.mock_data_client, expected_set_framework_actions, dry_run=dry_run)

    @pytest.mark.parametrize(
        # see above explanation of parameterization
        "reassess_passed_suppliers,reassess_failed_suppliers,reassess_failed_suppliers_draft_services,dry_run",
        tuple(product(*repeat((False, True,), 4))),
    )
    def test_without_draft_services_schema(
            self,
            reassess_passed_suppliers,
            reassess_failed_suppliers,
            reassess_failed_suppliers_draft_services,
            dry_run,
    ):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_discretionary_pass_schema=self._declaration_definite_pass_schema()["definitions"]["baseline"],
            service_schema=None,
            dry_run=dry_run,
            reassess_passed_suppliers=reassess_passed_suppliers,
            reassess_failed_suppliers=reassess_failed_suppliers,
            reassess_failed_draft_services=reassess_failed_suppliers_draft_services,
        )

        expected_set_framework_actions = (
            (2345, False),
            (3456, True),
            (4321, True),
            (4567, False),
            (5432, False),
            (6543, True),
            (8765, True),
        )

        _assert_set_framework_result_actions(self.mock_data_client, expected_set_framework_actions, dry_run=dry_run)

    @pytest.mark.parametrize(
        # see above explanation of parameterization
        "reassess_passed_suppliers,reassess_failed_suppliers,reassess_failed_suppliers_draft_services,dry_run",
        tuple(product(*repeat((False, True,), 4))),
    )
    def test_no_discretionary_pass_schema(
        self,
        reassess_passed_suppliers,
        reassess_failed_suppliers,
        reassess_failed_suppliers_draft_services,
        dry_run,
    ):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_discretionary_pass_schema=None,
            service_schema=self._draft_service_schema(),
            dry_run=dry_run,
            reassess_passed_suppliers=reassess_passed_suppliers,
            reassess_failed_suppliers=reassess_failed_suppliers,
            reassess_failed_draft_services=reassess_failed_suppliers_draft_services,
        )

        expected_set_framework_actions = (
            (3456, False),
            (4321, True),
            (4567, False),
            (5432, False),
            (6543, True),
            (8765, True),
        )
        expected_draft_services_actions = (
            (999003, False),
            (999005, False),
            (999012, False),
        )
        _assert_draft_service_result_actions(self.mock_data_client, expected_draft_services_actions, dry_run=dry_run)
        _assert_set_framework_result_actions(self.mock_data_client, expected_set_framework_actions, dry_run=dry_run)

    @pytest.mark.parametrize(
        # see above explanation of parameterization
        "reassess_passed_suppliers,reassess_failed_suppliers,reassess_failed_suppliers_draft_services,dry_run",
        tuple(product(*repeat((False, True,), 4))),
    )
    def test_neither_optional_schema(
        self,
        reassess_passed_suppliers,
        reassess_failed_suppliers,
        reassess_failed_suppliers_draft_services,
        dry_run,
    ):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_discretionary_pass_schema=None,
            service_schema=None,
            dry_run=dry_run,
            reassess_passed_suppliers=reassess_passed_suppliers,
            reassess_failed_suppliers=reassess_failed_suppliers,
            reassess_failed_draft_services=reassess_failed_suppliers_draft_services,
        )

        expected_set_framework_actions = (
            (3456, True),
            (4321, True),
            (4567, False),
            (5432, False),
            (6543, True),
            (8765, True),
        )

        _assert_set_framework_result_actions(self.mock_data_client, expected_set_framework_actions, dry_run=dry_run)


class TestPrevResults(BaseAssessmentMismatchedOnFrameworksTestMixin, BaseAssessmentTest):
    # it's very easy to flip some of the assertions for the dry_run mode so using parametrization here
    @pytest.mark.parametrize("dry_run", (False, True,),)
    def test_reassess_none(self, dry_run,):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_discretionary_pass_schema=self._declaration_definite_pass_schema()["definitions"]["baseline"],
            service_schema=self._draft_service_schema(),
            dry_run=dry_run,
            reassess_passed_suppliers=False,
            reassess_failed_suppliers=False,
            reassess_failed_draft_services=False,
        )

        expected_set_framework_actions = (
            (2345, False),
            (5432, False),
            (6543, False),
            (8765, True),
        )
        expected_draft_services_actions = (
            (999003, False),
        )
        _assert_draft_service_result_actions(self.mock_data_client, expected_draft_services_actions, dry_run=dry_run)
        _assert_set_framework_result_actions(self.mock_data_client, expected_set_framework_actions, dry_run=dry_run)

    # it's very easy to flip some of the assertions for the dry_run mode so using parametrization here
    @pytest.mark.parametrize("dry_run", (False, True,),)
    def test_reassess_failed_suppliers(self, dry_run,):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_discretionary_pass_schema=self._declaration_definite_pass_schema()["definitions"]["baseline"],
            service_schema=self._draft_service_schema(),
            dry_run=dry_run,
            reassess_passed_suppliers=False,
            reassess_failed_suppliers=True,
            reassess_failed_draft_services=False,
        )

        expected_set_framework_actions = (
            (2345, False),
            (4321, True),
            (5432, False),
            (6543, False),
            (8765, True),
        )
        expected_draft_services_actions = (
            (999003, False),
        )
        _assert_draft_service_result_actions(self.mock_data_client, expected_draft_services_actions, dry_run=dry_run)
        _assert_set_framework_result_actions(self.mock_data_client, expected_set_framework_actions, dry_run=dry_run)

    # it's very easy to flip some of the assertions for the dry_run mode so using parametrization here
    @pytest.mark.parametrize("dry_run", (False, True,),)
    def test_reassess_passed_suppliers(self, dry_run,):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_discretionary_pass_schema=self._declaration_definite_pass_schema()["definitions"]["baseline"],
            service_schema=self._draft_service_schema(),
            dry_run=dry_run,
            reassess_passed_suppliers=True,
            reassess_failed_suppliers=False,
            reassess_failed_draft_services=False,
        )

        expected_set_framework_actions = (
            (2345, False),
            (3456, False),
            (5432, False),
            (6543, False),
            (8765, True),
        )
        expected_draft_services_actions = (
            (999003, False),
            (999005, False),
        )
        _assert_draft_service_result_actions(self.mock_data_client, expected_draft_services_actions, dry_run=dry_run)
        _assert_set_framework_result_actions(self.mock_data_client, expected_set_framework_actions, dry_run=dry_run)

    # it's very easy to flip some of the assertions for the dry_run mode so using parametrization here
    @pytest.mark.parametrize("dry_run", (False, True,),)
    def test_reassess_all(self, dry_run,):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_discretionary_pass_schema=self._declaration_definite_pass_schema()["definitions"]["baseline"],
            service_schema=self._draft_service_schema(),
            dry_run=dry_run,
            reassess_passed_suppliers=True,
            reassess_failed_suppliers=True,
            reassess_failed_draft_services=True,
        )

        expected_set_framework_actions = (
            (2345, False),
            (3456, False),
            (4321, True),
            (5432, False),
            (6543, True),
            (8765, True),
        )
        expected_draft_services_actions = (
            (999003, False),
            (999005, False),
            (999010, True),
            (999014, True),
        )
        _assert_draft_service_result_actions(self.mock_data_client, expected_draft_services_actions, dry_run=dry_run)
        _assert_set_framework_result_actions(self.mock_data_client, expected_set_framework_actions, dry_run=dry_run)

    # it's very easy to flip some of the assertions for the dry_run mode so using parametrization here
    @pytest.mark.parametrize("dry_run", (False, True,),)
    def test_reassess_all_no_service_schema(self, dry_run,):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_discretionary_pass_schema=self._declaration_definite_pass_schema()["definitions"]["baseline"],
            service_schema=None,
            dry_run=dry_run,
            reassess_passed_suppliers=True,
            reassess_failed_suppliers=True,
            reassess_failed_draft_services=True,
        )

        expected_set_framework_actions = (
            (2345, False),
            (4321, True),
            (5432, False),
            (6543, True),
            (8765, True),
        )
        expected_draft_services_actions = (
            (999010, True),
            (999012, True),
            (999014, True),
        )
        _assert_draft_service_result_actions(self.mock_data_client, expected_draft_services_actions, dry_run=dry_run)
        _assert_set_framework_result_actions(self.mock_data_client, expected_set_framework_actions, dry_run=dry_run)
