import pytest

from itertools import product, repeat

from dmscripts.mark_definite_framework_results import mark_definite_framework_results

from .assessment_helpers import BaseAssessmentTest


class _BaseMarkResultsTest(BaseAssessmentTest):
    def _assert_actions(self, expected_sf_actions, expected_ds_actions, dry_run=False):
        # comparing these with the order normalized because we don't really care about that - unless of course the same
        # object is being written to twice (and hence overwritten) - but that's not a desired behaviour anyway and
        # it wouldn't be something sensible to assert for.
        assert sorted(self.mock_data_client.set_framework_result.call_args_list, key=lambda c: c[0]) == (sorted((
            ((k, "h-cloud-99", act, "Blazes Boylan"), {},) for k, act in expected_sf_actions.items()
        ), key=lambda c: c[0]) if not dry_run else [])
        assert sorted(self.mock_data_client.update_draft_service_status.call_args_list, key=lambda c: c[0]) == (sorted((
            ((k, "submitted" if act else "failed", "Blazes Boylan"), {},) for k, act in expected_ds_actions.items()
        ), key=lambda c: c[0]) if not dry_run else [])


class TestNoPrevResults(_BaseMarkResultsTest):
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
        # we can very easily parametrize this into the 16 possible combinations of these flags - the results for the first
        # three flags should be identical and it's very easy to flip some of the assertions for the dry_run mode
        "reassess_passed,reassess_failed,reassess_failed_ds,dry_run",
        tuple(product(*repeat((False, True,), 4))),
    )
    def test_with_ds_schema(self, reassess_passed, reassess_failed, reassess_failed_ds, dry_run,):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_baseline_schema=self._declaration_definite_pass_schema()["definitions"]["baseline"],
            service_schema=self._draft_service_schema(),
            dry_run=dry_run,
            reassess_passed=reassess_passed,
            reassess_failed=reassess_failed,
            reassess_failed_draft_services=reassess_failed_ds,
        )

        expected_sf_actions = {
            2345: False,
            3456: False,
            4321: True,
            4567: False,
            5432: False,
            6543: True,
            8765: True,
        }
        expected_ds_actions = {
            999003: False,
            999005: False,
            999012: False,
        }
        self._assert_actions(expected_sf_actions, expected_ds_actions, dry_run=dry_run)

    @pytest.mark.parametrize(
        # see above explanation of parameterization
        "reassess_passed,reassess_failed,reassess_failed_ds,dry_run",
        tuple(product(*repeat((False, True,), 4))),
    )
    def test_without_ds_schema(self, reassess_passed, reassess_failed, reassess_failed_ds, dry_run,):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_baseline_schema=self._declaration_definite_pass_schema()["definitions"]["baseline"],
            service_schema=None,
            dry_run=dry_run,
            reassess_passed=reassess_passed,
            reassess_failed=reassess_failed,
            reassess_failed_draft_services=reassess_failed_ds,
        )

        expected_sf_actions = {
            2345: False,
            3456: True,
            4321: True,
            4567: False,
            5432: False,
            6543: True,
            8765: True,
        }
        expected_ds_actions = {}
        self._assert_actions(expected_sf_actions, expected_ds_actions, dry_run=dry_run)

    @pytest.mark.parametrize(
        # see above explanation of parameterization
        "reassess_passed,reassess_failed,reassess_failed_ds,dry_run",
        tuple(product(*repeat((False, True,), 4))),
    )
    def test_no_baseline_schema(
            self,
            reassess_passed,
            reassess_failed,
            reassess_failed_ds,
            dry_run,
            ):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_baseline_schema=None,
            service_schema=self._draft_service_schema(),
            dry_run=dry_run,
            reassess_passed=reassess_passed,
            reassess_failed=reassess_failed,
            reassess_failed_draft_services=reassess_failed_ds,
        )

        expected_sf_actions = {
            3456: False,
            4321: True,
            4567: False,
            5432: False,
            6543: True,
            8765: True,
        }
        expected_ds_actions = {
            999003: False,
            999005: False,
            999012: False,
        }
        self._assert_actions(expected_sf_actions, expected_ds_actions, dry_run=dry_run)

    @pytest.mark.parametrize(
        # see above explanation of parameterization
        "reassess_passed,reassess_failed,reassess_failed_ds,dry_run",
        tuple(product(*repeat((False, True,), 4))),
    )
    def test_neither_optional_schema(
            self,
            reassess_passed,
            reassess_failed,
            reassess_failed_ds,
            dry_run,
            ):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_baseline_schema=None,
            service_schema=None,
            dry_run=dry_run,
            reassess_passed=reassess_passed,
            reassess_failed=reassess_failed,
            reassess_failed_draft_services=reassess_failed_ds,
        )

        expected_sf_actions = {
            3456: True,
            4321: True,
            4567: False,
            5432: False,
            6543: True,
            8765: True,
        }
        expected_ds_actions = {}
        self._assert_actions(expected_sf_actions, expected_ds_actions, dry_run=dry_run)


class TestPrevResults(_BaseMarkResultsTest):
    # it's very easy to flip some of the assertions for the dry_run mode so using parametrization here
    @pytest.mark.parametrize("dry_run", (False, True,),)
    def test_reassess_none(self, dry_run,):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_baseline_schema=self._declaration_definite_pass_schema()["definitions"]["baseline"],
            service_schema=self._draft_service_schema(),
            dry_run=dry_run,
            reassess_passed=False,
            reassess_failed=False,
            reassess_failed_draft_services=False,
        )

        expected_sf_actions = {
            2345: False,
            5432: False,
            6543: False,
            8765: True,
        }
        expected_ds_actions = {
            999003: False,
        }
        self._assert_actions(expected_sf_actions, expected_ds_actions, dry_run=dry_run)

    # it's very easy to flip some of the assertions for the dry_run mode so using parametrization here
    @pytest.mark.parametrize("dry_run", (False, True,),)
    def test_reassess_failed(self, dry_run,):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_baseline_schema=self._declaration_definite_pass_schema()["definitions"]["baseline"],
            service_schema=self._draft_service_schema(),
            dry_run=dry_run,
            reassess_passed=False,
            reassess_failed=True,
            reassess_failed_draft_services=False,
        )

        expected_sf_actions = {
            2345: False,
            4321: True,
            5432: False,
            6543: False,
            8765: True,
        }
        expected_ds_actions = {
            999003: False,
        }
        self._assert_actions(expected_sf_actions, expected_ds_actions, dry_run=dry_run)

    # it's very easy to flip some of the assertions for the dry_run mode so using parametrization here
    @pytest.mark.parametrize("dry_run", (False, True,),)
    def test_reassess_passed(self, dry_run,):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_baseline_schema=self._declaration_definite_pass_schema()["definitions"]["baseline"],
            service_schema=self._draft_service_schema(),
            dry_run=dry_run,
            reassess_passed=True,
            reassess_failed=False,
            reassess_failed_draft_services=False,
        )

        expected_sf_actions = {
            2345: False,
            3456: False,
            5432: False,
            6543: False,
            8765: True,
        }
        expected_ds_actions = {
            999003: False,
            999005: False,
        }
        self._assert_actions(expected_sf_actions, expected_ds_actions, dry_run=dry_run)

    # it's very easy to flip some of the assertions for the dry_run mode so using parametrization here
    @pytest.mark.parametrize("dry_run", (False, True,),)
    def test_reassess_all(self, dry_run,):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_baseline_schema=self._declaration_definite_pass_schema()["definitions"]["baseline"],
            service_schema=self._draft_service_schema(),
            dry_run=dry_run,
            reassess_passed=True,
            reassess_failed=True,
            reassess_failed_draft_services=True,
        )

        expected_sf_actions = {
            2345: False,
            3456: False,
            4321: True,
            5432: False,
            6543: True,
            8765: True,
        }
        expected_ds_actions = {
            999003: False,
            999005: False,
            999010: True,
            999014: True,
        }
        self._assert_actions(expected_sf_actions, expected_ds_actions, dry_run=dry_run)

    # it's very easy to flip some of the assertions for the dry_run mode so using parametrization here
    @pytest.mark.parametrize("dry_run", (False, True,),)
    def test_reassess_all_no_service_schema(self, dry_run,):
        mark_definite_framework_results(
            self.mock_data_client,
            "Blazes Boylan",
            "h-cloud-99",
            self._declaration_definite_pass_schema(),
            declaration_baseline_schema=self._declaration_definite_pass_schema()["definitions"]["baseline"],
            service_schema=None,
            dry_run=dry_run,
            reassess_passed=True,
            reassess_failed=True,
            reassess_failed_draft_services=True,
        )

        expected_sf_actions = {
            2345: False,
            4321: True,
            5432: False,
            6543: True,
            8765: True,
        }
        expected_ds_actions = {
            999010: True,
            999012: True,
            999014: True,
        }
        self._assert_actions(expected_sf_actions, expected_ds_actions, dry_run=dry_run)
