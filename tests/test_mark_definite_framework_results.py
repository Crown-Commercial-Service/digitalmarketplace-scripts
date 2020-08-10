import pytest

from itertools import product, repeat

from dmscripts.mark_definite_framework_results import mark_definite_framework_results

from .assessment_helpers import BaseAssessmentTest, BaseAssessmentMismatchedOnFrameworksTestMixin


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

    @pytest.mark.parametrize(
        # see above explanation of parameterization
        "reassess_passed_suppliers,reassess_failed_suppliers,dry_run",
        tuple(product(*repeat((False, True,), 3))),
    )
    def test_with_discretionary_pass_schema(
            self,
            reassess_passed_suppliers,
            reassess_failed_suppliers,
            dry_run,
    ):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_discretionary_pass_schema=self._declaration_definite_pass_schema()["definitions"]["baseline"],
            dry_run=dry_run,
            reassess_passed_suppliers=reassess_passed_suppliers,
            reassess_failed_suppliers=reassess_failed_suppliers,
        )

        expected_set_framework_actions = (
            (2345, False),
            (3456, True),
            (4321, True),
            (4567, False),
            (5432, False),
            (8765, True),
        )

        _assert_set_framework_result_actions(self.mock_data_client, expected_set_framework_actions, dry_run=dry_run)

    @pytest.mark.parametrize(
        # see above explanation of parameterization
        "reassess_passed_suppliers,reassess_failed_suppliers,dry_run",
        tuple(product(*repeat((False, True,), 3))),
    )
    def test_no_discretionary_pass_schema(
        self,
        reassess_passed_suppliers,
        reassess_failed_suppliers,
        dry_run,
    ):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_discretionary_pass_schema=None,
            dry_run=dry_run,
            reassess_passed_suppliers=reassess_passed_suppliers,
            reassess_failed_suppliers=reassess_failed_suppliers,
        )

        expected_set_framework_actions = (
            (3456, True),
            (4321, True),
            (4567, False),
            (5432, False),
            (8765, True),
        )
        _assert_set_framework_result_actions(self.mock_data_client, expected_set_framework_actions, dry_run=dry_run)

    @pytest.mark.parametrize(
        # see above explanation of parameterization
        "reassess_passed_suppliers,reassess_failed_suppliers,dry_run",
        tuple(product(*repeat((False, True,), 3))),
    )
    def test_neither_optional_schema(
        self,
        reassess_passed_suppliers,
        reassess_failed_suppliers,
        dry_run,
    ):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_discretionary_pass_schema=None,
            dry_run=dry_run,
            reassess_passed_suppliers=reassess_passed_suppliers,
            reassess_failed_suppliers=reassess_failed_suppliers,
        )

        expected_set_framework_actions = (
            (3456, True),
            (4321, True),
            (4567, False),
            (5432, False),
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
            dry_run=dry_run,
            reassess_passed_suppliers=False,
            reassess_failed_suppliers=False,
        )

        expected_set_framework_actions = (
            (2345, False),
            (5432, False),
            (8765, True),
        )
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
            dry_run=dry_run,
            reassess_passed_suppliers=False,
            reassess_failed_suppliers=True,
        )

        expected_set_framework_actions = (
            (2345, False),
            (4321, True),
            (5432, False),
            (8765, True),
        )
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
            dry_run=dry_run,
            reassess_passed_suppliers=True,
            reassess_failed_suppliers=False,
        )

        expected_set_framework_actions = (
            (2345, False),
            (5432, False),
            (8765, True),
        )
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
            dry_run=dry_run,
            reassess_passed_suppliers=True,
            reassess_failed_suppliers=True,
        )

        expected_set_framework_actions = (
            (2345, False),
            (4321, True),
            (5432, False),
            (8765, True),
        )
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
            dry_run=dry_run,
            reassess_passed_suppliers=True,
            reassess_failed_suppliers=True,
        )

        expected_set_framework_actions = (
            (2345, False),
            (4321, True),
            (5432, False),
            (8765, True),
        )
        _assert_set_framework_result_actions(self.mock_data_client, expected_set_framework_actions, dry_run=dry_run)
