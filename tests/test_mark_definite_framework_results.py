from functools import partial
from itertools import chain, product, repeat


import pytest


from dmscripts.mark_definite_framework_results import mark_definite_framework_results
from dmscripts.logging import configure_logger, DEBUG as loglevel_DEBUG


# putting these in lambdas so we are sure to always get a clean copy
_declaration_definite_pass_schema = lambda: {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "allOf": [
        {"$ref": "#/definitions/notDefiniteFail"},
        {
            "properties": {
                "shouldBeFalseLax": {"enum": [False]},
                "shouldBeTrueLax": {"enum": [True]},
                "shouldMatchPatternLax": {
                    "type": "string",
                    "pattern": "^Good +[Pp]attern",
                },
            },
        },
    ],
    "definitions": {
        "notDefiniteFail": {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "properties": {
                "status": {"enum": ["complete"]},
                "shouldBeFalseStrict": {"enum": [False]},
                "shouldBeTrueStrict": {"enum": [True]},
                "shouldMatchPatternStrict": {
                    "type": "string",
                    "pattern": "^H.? *E.? *L.? *Y.? *S?",
                },
            },
        },
    },
}
_draft_service_schema = lambda: {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "anyOf": [
        {
            "properties": {
                "lotSlug": {"enum": ["stuffed-roast-heart"]},
                "kosher": {"type": "boolean"},
            },
            "required": ["kosher"],
        },
        {
            "properties": {
                "lotSlug": {"enum": ["pork-kidney", "ham-and-eggs"]},
                "kosher": {"enum": [False]},
                "butcher": {"enum": ["Dlugacz"]},
            },
        },
        {
            "properties": {
                "lotSlug": {"enum": ["grilled-mutton-kidney"]},
            },
        },
    ],
}
_base_supplier_frameworks = lambda framework_slug: {k: dict(v, supplierId=k, frameworkSlug=framework_slug) for k, v in {
    # this has many fields filled out, the intention being to take a quick dict comprehension-modified copy blanket-
    # overriding any undesired values where necessary
    1234: {
        "onFramework": True,
        "declaration": {
            "status": "complete",
            "shouldBeFalseLax": True,
            "shouldBeTrueStrict": True,
            "shouldMatchPatternStrict": "HE L Y   S",
            "irrelevantQuestion": "Irrelevant answer",
        },
    },
    2345: {
        "onFramework": None,
        "declaration": {
            "status": "complete",
            "shouldBeTrueLax": True,
            "shouldMatchPatternLax": "Good pattern",
            "shouldBeFalseStrict": None,  # <- subtle but important test here
        },
    },
    3456: {
        "onFramework": True,
        "declaration": {
            "status": "complete",
        },
    },
    4321: {
        "onFramework": False,
        "declaration": {
            "status": "complete",
            "shouldBeTrueLax": True,
            "shouldMatchPatternLax": "Good   Pattern",
            "shouldMatchPatternStrict": "H.E. L.  Y",
            "irrelevantStupidQuestion": "Irrelevant stupid answer",
        },
    },
    4567: {
        "onFramework": False,
        "declaration": {
            "status": "bored-gave-up",
            "shouldBeTrueStrict": True,
        },
    },
    5432: {
        "onFramework": None,
        "declaration": {
            "status": "complete",
            "shouldBeFalseLax": True,
            "shouldMatchPatternStrict": "HEL Y...",
        },
    },
    6543: {
        "onFramework": None,
        "declaration": {
            "status": "complete",
            "shouldBeTrueStrict": True,
        },
    },
    7654: {
        "onFramework": None,
        "declaration": {
            "status": "complete",
            "shouldBeFalseLax": True,
        },
    },
    8765: {
        "onFramework": None,
        "declaration": {
            "status": "complete",
            "shouldBeFalseLax": False,
            "shouldBeTrueStrict": True,
            "shouldMatchPatternLax": "Good    pattern",
        },
    },
}.items()}
_base_draft_services = lambda framework_slug: {
    s_id: tuple(dict(s, supplierId=s_id, frameworkSlug=framework_slug) for s in v) for s_id, v in {
        1234: (
            {
                "id": 999001,
                "status": "submitted",
                "lotSlug": "stuffed-roast-heart",
                "kosher": False,
            },
        ),
        2345: (
            {
                "id": 999002,
                "status": "submitted",
                "lotSlug": "ham-and-eggs",
                "butcher": "Dlugacz",
            },
            {
                "id": 999003,
                "status": "submitted",
                "lotSlug": "ham-and-eggs",
                "kosher": True,
            },
            {
                "id": 999004,
                "status": "submitted",
                "lotSlug": "pork-kidney",
                "kosher": False,
            },
        ),
        3456: (
            {
                "id": 999005,
                "status": "submitted",
                "lotSlug": "stuffed-roast-heart",
            },
        ),
        4321: (
            {
                "id": 999006,
                "status": "submitted",
                "lotSlug": "grilled-mutton-kidney",
                "butcher": "Buckley",
            },
            {
                "id": 999007,
                "status": "submitted",
                "lotSlug": "pork-kidney",
                "butcher": "Dlugacz",
                "kosher": False,
            },
        ),
        4567: (
            {
                "id": 999008,
                "status": "not-submitted",
                "lotSlug": "grilled-mutton-kidney",
            },
            {
                "id": 999009,
                "status": "submitted",
                "lotSlug": "ham-and-eggs",
                "anotherIrrelevantQuestion": "Another irrelevant answer",
            },
        ),
        5432: (),
        6543: (
            {
                "id": 999010,
                "status": "failed",
                "lotSlug": "stuffed-roast-heart",
                "kosher": True,
            },
        ),
        7654: (
            {
                "id": 999011,
                "status": "submitted",
                "lotSlug": "pork-kidney",
            },
            {
                "id": 999012,
                "status": "failed",
                "lotSlug": "stuffed-roast-heart",
                "kosher": None,
            },
        ),
        8765: (
            {
                "id": 999013,
                "status": "submitted",
                "lotSlug": "stuffed-roast-heart",
                "kosher": False,
            },
            {
                "id": 999014,
                "status": "failed",
                "lotSlug": "grilled-mutton-kidney",
                "kosher": None,
            },
            {
                "id": 999015,
                "status": "submitted",
                "lotSlug": "ham-and-eggs",
                "butcher": "Dlugacz",
                "kosher": False,
            },
            {
                "id": 999016,
                "status": "submitted",
                "lotSlug": "stuffed-roast-heart",
                "kosher": True,
            },
        ),
    }.items()
}


def _mock_get_supplier_framework_info(mandated_framework_slug, sf_dict, supplier_id, framework_slug,):
    assert framework_slug == mandated_framework_slug
    return {
        "frameworkInterest": sf_dict[supplier_id],
    }


def _mock_get_interested_suppliers(mandated_framework_slug, sf_dict, framework_slug):
    assert framework_slug == mandated_framework_slug
    return {
        "interestedSuppliers": sf_dict.keys(),
    }


def _mock_find_draft_services_iter(mandated_framework_slug, ds_dict, supplier_id, framework=None):
    assert framework == mandated_framework_slug
    return iter(ds_dict[supplier_id])


def _setup_GET_mocks(mock_data_client, mock_supplier_frameworks, mock_draft_services):
    mock_data_client.get_supplier_framework_info.side_effect = partial(
        _mock_get_supplier_framework_info,
        "h-cloud-99",
        mock_supplier_frameworks,
    )
    mock_data_client.get_interested_suppliers.side_effect = partial(
        _mock_get_interested_suppliers,
        "h-cloud-99",
        mock_supplier_frameworks,
    )
    mock_data_client.find_draft_services_iter.side_effect = partial(
        _mock_find_draft_services_iter,
        "h-cloud-99",
        mock_draft_services,
    )


def _assert_actions(mock_data_client, expected_sf_actions, expected_ds_actions, dry_run=False):
    # comparing these with the order normalized because we don't really care about that - unless of course the same
    # object is being written to twice (and hence overwritten) - but that's not a desired behaviour anyway and
    # it wouldn't be something sensible to assert for.
    assert sorted(mock_data_client.set_framework_result.call_args_list, key=lambda c: c[0]) == (sorted((
        ((k, "h-cloud-99", act, "Blazes Boylan"), {},) for k, act in expected_sf_actions.items() if act is not None
    ), key=lambda c: c[0]) if not dry_run else [])
    assert sorted(mock_data_client.update_draft_service_status.call_args_list, key=lambda c: c[0]) == (sorted((
        ((k, "submitted" if act else "failed", "Blazes Boylan"), {},)
        for k, act in expected_ds_actions.items() if act is not None
    ), key=lambda c: c[0]) if not dry_run else [])


@pytest.mark.parametrize(
    # we can very easily parametrize this into the 16 possible combinations of these flags - the results for the first
    # three flags should be identical and it's very easy to flip some of the assertions for the dry_run mode
    "reassess_passed,reassess_failed,reassess_failed_ds,dry_run",
    tuple(product(*repeat((False, True,), 4))),
)
def test_no_prev_results(mock_data_client, reassess_passed, reassess_failed, reassess_failed_ds, dry_run,):
    # no onFramework values should be set yet
    mock_supplier_frameworks = {
        k: dict(v, onFramework=None) for k, v in _base_supplier_frameworks("h-cloud-99").items()
    }
    # no draft services should have been failed yet
    mock_draft_services = {
        k: tuple(
            dict(s, status=("submitted" if s["status"] == "failed" else s["status"])) for s in v
        ) for k, v in _base_draft_services("h-cloud-99").items()
    }
    _setup_GET_mocks(mock_data_client, mock_supplier_frameworks, mock_draft_services)

    mark_definite_framework_results(
        mock_data_client,
        "Blazes Boylan",
        "h-cloud-99",
        _declaration_definite_pass_schema(),
        declaration_not_definite_fail_schema=_declaration_definite_pass_schema()["definitions"]["notDefiniteFail"],
        service_schema=_draft_service_schema(),
        dry_run=dry_run,
        reassess_passed=reassess_passed,
        reassess_failed=reassess_failed,
        reassess_failed_draft_services=reassess_failed_ds,
    )

    expected_sf_actions = dict(((k, None) for k in mock_supplier_frameworks.keys()), **{
        2345: False,
        3456: False,
        4321: True,
        4567: False,
        5432: False,
        6543: True,
        8765: True,
    })
    expected_ds_actions = dict(((k, None) for k in (chain.from_iterable(v) for v in mock_draft_services.values())), **{
        999003: False,
        999005: False,
        999012: False,
    })
    _assert_actions(mock_data_client, expected_sf_actions, expected_ds_actions, dry_run=dry_run)


@pytest.mark.parametrize(
    # see above explanation of parameterization
    "reassess_passed,reassess_failed,reassess_failed_ds,dry_run",
    tuple(product(*repeat((False, True,), 4))),
)
def test_no_prev_results_no_ds_schema(mock_data_client, reassess_passed, reassess_failed, reassess_failed_ds, dry_run,):
    # no onFramework values should be set yet
    mock_supplier_frameworks = {
        k: dict(v, onFramework=None) for k, v in _base_supplier_frameworks("h-cloud-99").items()
    }
    # no draft services should have been failed yet
    mock_draft_services = {
        k: tuple(
            dict(s, status=("submitted" if s["status"] == "failed" else s["status"])) for s in v
        ) for k, v in _base_draft_services("h-cloud-99").items()
    }
    _setup_GET_mocks(mock_data_client, mock_supplier_frameworks, mock_draft_services)

    mark_definite_framework_results(
        mock_data_client,
        "Blazes Boylan",
        "h-cloud-99",
        _declaration_definite_pass_schema(),
        declaration_not_definite_fail_schema=_declaration_definite_pass_schema()["definitions"]["notDefiniteFail"],
        service_schema=None,
        dry_run=dry_run,
        reassess_passed=reassess_passed,
        reassess_failed=reassess_failed,
        reassess_failed_draft_services=reassess_failed_ds,
    )

    expected_sf_actions = dict(((k, None) for k in mock_supplier_frameworks.keys()), **{
        2345: False,
        3456: True,
        4321: True,
        4567: False,
        5432: False,
        6543: True,
        8765: True,
    })
    expected_ds_actions = dict(((k, None) for k in (chain.from_iterable(v) for v in mock_draft_services.values())))
    _assert_actions(mock_data_client, expected_sf_actions, expected_ds_actions, dry_run=dry_run)


@pytest.mark.parametrize(
    # see above explanation of parameterization
    "reassess_passed,reassess_failed,reassess_failed_ds,dry_run",
    tuple(product(*repeat((False, True,), 4))),
)
def test_no_prev_results_no_not_definite_fail_schema(
        mock_data_client,
        reassess_passed,
        reassess_failed,
        reassess_failed_ds,
        dry_run,
        ):
    # no onFramework values should be set yet
    mock_supplier_frameworks = {
        k: dict(v, onFramework=None) for k, v in _base_supplier_frameworks("h-cloud-99").items()
    }
    # no draft services should have been failed yet
    mock_draft_services = {
        k: tuple(
            dict(s, status=("submitted" if s["status"] == "failed" else s["status"])) for s in v
        ) for k, v in _base_draft_services("h-cloud-99").items()
    }
    _setup_GET_mocks(mock_data_client, mock_supplier_frameworks, mock_draft_services)

    mark_definite_framework_results(
        mock_data_client,
        "Blazes Boylan",
        "h-cloud-99",
        _declaration_definite_pass_schema(),
        declaration_not_definite_fail_schema=None,
        service_schema=_draft_service_schema(),
        dry_run=dry_run,
        reassess_passed=reassess_passed,
        reassess_failed=reassess_failed,
        reassess_failed_draft_services=reassess_failed_ds,
    )

    expected_sf_actions = dict(((k, None) for k in mock_supplier_frameworks.keys()), **{
        3456: False,
        4321: True,
        5432: False,
        6543: True,
        8765: True,
    })
    expected_ds_actions = dict(((k, None) for k in (chain.from_iterable(v) for v in mock_draft_services.values())), **{
        999003: False,
        999005: False,
        999012: False,
    })
    _assert_actions(mock_data_client, expected_sf_actions, expected_ds_actions, dry_run=dry_run)


@pytest.mark.parametrize(
    # see above explanation of parameterization
    "reassess_passed,reassess_failed,reassess_failed_ds,dry_run",
    tuple(product(*repeat((False, True,), 4))),
)
def test_no_prev_results_neither_optional_schema(
        mock_data_client,
        reassess_passed,
        reassess_failed,
        reassess_failed_ds,
        dry_run,
        ):
    # no onFramework values should be set yet
    mock_supplier_frameworks = {
        k: dict(v, onFramework=None) for k, v in _base_supplier_frameworks("h-cloud-99").items()
    }
    # no draft services should have been failed yet
    mock_draft_services = {
        k: tuple(
            dict(s, status=("submitted" if s["status"] == "failed" else s["status"])) for s in v
        ) for k, v in _base_draft_services("h-cloud-99").items()
    }
    _setup_GET_mocks(mock_data_client, mock_supplier_frameworks, mock_draft_services)

    mark_definite_framework_results(
        mock_data_client,
        "Blazes Boylan",
        "h-cloud-99",
        _declaration_definite_pass_schema(),
        declaration_not_definite_fail_schema=None,
        service_schema=None,
        dry_run=dry_run,
        reassess_passed=reassess_passed,
        reassess_failed=reassess_failed,
        reassess_failed_draft_services=reassess_failed_ds,
    )

    expected_sf_actions = dict(((k, None) for k in mock_supplier_frameworks.keys()), **{
        3456: True,
        4321: True,
        5432: False,
        6543: True,
        8765: True,
    })
    expected_ds_actions = dict(((k, None) for k in (chain.from_iterable(v) for v in mock_draft_services.values())))
    _assert_actions(mock_data_client, expected_sf_actions, expected_ds_actions, dry_run=dry_run)


# it's very easy to flip some of the assertions for the dry_run mode so using parametrization here
@pytest.mark.parametrize("dry_run", (False, True,),)
def test_prev_results_reassess_none(mock_data_client, dry_run,):
    mock_supplier_frameworks = _base_supplier_frameworks("h-cloud-99")
    mock_draft_services = _base_draft_services("h-cloud-99")
    _setup_GET_mocks(mock_data_client, mock_supplier_frameworks, mock_draft_services)

    mark_definite_framework_results(
        mock_data_client,
        "Blazes Boylan",
        "h-cloud-99",
        _declaration_definite_pass_schema(),
        declaration_not_definite_fail_schema=_declaration_definite_pass_schema()["definitions"]["notDefiniteFail"],
        service_schema=_draft_service_schema(),
        dry_run=dry_run,
        reassess_passed=False,
        reassess_failed=False,
        reassess_failed_draft_services=False,
    )

    expected_sf_actions = dict(((k, None) for k in mock_supplier_frameworks.keys()), **{
        2345: False,
        5432: False,
        6543: False,
        8765: True,
    })
    expected_ds_actions = dict(((k, None) for k in (chain.from_iterable(v) for v in mock_draft_services.values())), **{
        999003: False,
    })
    _assert_actions(mock_data_client, expected_sf_actions, expected_ds_actions, dry_run=dry_run)


# it's very easy to flip some of the assertions for the dry_run mode so using parametrization here
@pytest.mark.parametrize("dry_run", (False, True,),)
def test_prev_results_reassess_failed(mock_data_client, dry_run,):
    mock_supplier_frameworks = _base_supplier_frameworks("h-cloud-99")
    mock_draft_services = _base_draft_services("h-cloud-99")
    _setup_GET_mocks(mock_data_client, mock_supplier_frameworks, mock_draft_services)

    mark_definite_framework_results(
        mock_data_client,
        "Blazes Boylan",
        "h-cloud-99",
        _declaration_definite_pass_schema(),
        declaration_not_definite_fail_schema=_declaration_definite_pass_schema()["definitions"]["notDefiniteFail"],
        service_schema=_draft_service_schema(),
        dry_run=dry_run,
        reassess_passed=False,
        reassess_failed=True,
        reassess_failed_draft_services=False,
    )

    expected_sf_actions = dict(((k, None) for k in mock_supplier_frameworks.keys()), **{
        2345: False,
        4321: True,
        5432: False,
        6543: False,
        8765: True,
    })
    expected_ds_actions = dict(((k, None) for k in (chain.from_iterable(v) for v in mock_draft_services.values())), **{
        999003: False,
    })
    _assert_actions(mock_data_client, expected_sf_actions, expected_ds_actions, dry_run=dry_run)


# it's very easy to flip some of the assertions for the dry_run mode so using parametrization here
@pytest.mark.parametrize("dry_run", (False, True,),)
def test_prev_results_reassess_passed(mock_data_client, dry_run,):
    mock_supplier_frameworks = _base_supplier_frameworks("h-cloud-99")
    mock_draft_services = _base_draft_services("h-cloud-99")
    _setup_GET_mocks(mock_data_client, mock_supplier_frameworks, mock_draft_services)

    mark_definite_framework_results(
        mock_data_client,
        "Blazes Boylan",
        "h-cloud-99",
        _declaration_definite_pass_schema(),
        declaration_not_definite_fail_schema=_declaration_definite_pass_schema()["definitions"]["notDefiniteFail"],
        service_schema=_draft_service_schema(),
        dry_run=dry_run,
        reassess_passed=True,
        reassess_failed=False,
        reassess_failed_draft_services=False,
    )

    expected_sf_actions = dict(((k, None) for k in mock_supplier_frameworks.keys()), **{
        2345: False,
        3456: False,
        5432: False,
        6543: False,
        8765: True,
    })
    expected_ds_actions = dict(((k, None) for k in (chain.from_iterable(v) for v in mock_draft_services.values())), **{
        999003: False,
        999005: False,
    })
    _assert_actions(mock_data_client, expected_sf_actions, expected_ds_actions, dry_run=dry_run)


# it's very easy to flip some of the assertions for the dry_run mode so using parametrization here
@pytest.mark.parametrize("dry_run", (False, True,),)
def test_prev_results_reassess_all(mock_data_client, dry_run,):
    mock_supplier_frameworks = _base_supplier_frameworks("h-cloud-99")
    mock_draft_services = _base_draft_services("h-cloud-99")
    _setup_GET_mocks(mock_data_client, mock_supplier_frameworks, mock_draft_services)

    mark_definite_framework_results(
        mock_data_client,
        "Blazes Boylan",
        "h-cloud-99",
        _declaration_definite_pass_schema(),
        declaration_not_definite_fail_schema=_declaration_definite_pass_schema()["definitions"]["notDefiniteFail"],
        service_schema=_draft_service_schema(),
        dry_run=dry_run,
        reassess_passed=True,
        reassess_failed=True,
        reassess_failed_draft_services=True,
    )

    expected_sf_actions = dict(((k, None) for k in mock_supplier_frameworks.keys()), **{
        2345: False,
        3456: False,
        4321: True,
        5432: False,
        6543: True,
        8765: True,
    })
    expected_ds_actions = dict(((k, None) for k in (chain.from_iterable(v) for v in mock_draft_services.values())), **{
        999003: False,
        999005: False,
        999010: True,
        999014: True,
    })
    _assert_actions(mock_data_client, expected_sf_actions, expected_ds_actions, dry_run=dry_run)


# it's very easy to flip some of the assertions for the dry_run mode so using parametrization here
@pytest.mark.parametrize("dry_run", (False, True,),)
def test_prev_results_reassess_all_no_service_schema(mock_data_client, dry_run,):
    mock_supplier_frameworks = _base_supplier_frameworks("h-cloud-99")
    mock_draft_services = _base_draft_services("h-cloud-99")
    _setup_GET_mocks(mock_data_client, mock_supplier_frameworks, mock_draft_services)

    mark_definite_framework_results(
        mock_data_client,
        "Blazes Boylan",
        "h-cloud-99",
        _declaration_definite_pass_schema(),
        declaration_not_definite_fail_schema=_declaration_definite_pass_schema()["definitions"]["notDefiniteFail"],
        service_schema=None,
        dry_run=dry_run,
        reassess_passed=True,
        reassess_failed=True,
        reassess_failed_draft_services=True,
    )

    expected_sf_actions = dict(((k, None) for k in mock_supplier_frameworks.keys()), **{
        2345: False,
        4321: True,
        5432: False,
        6543: True,
        8765: True,
    })
    expected_ds_actions = dict(((k, None) for k in (chain.from_iterable(v) for v in mock_draft_services.values())), **{
        999010: True,
        999012: True,
        999014: True,
    })
    _assert_actions(mock_data_client, expected_sf_actions, expected_ds_actions, dry_run=dry_run)
