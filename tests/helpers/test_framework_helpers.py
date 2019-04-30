import pytest
from collections import Counter
from mock import Mock, call

from dmapiclient import HTTPError
import dmscripts.helpers.framework_helpers as framework_helpers


def test_get_submitted_drafts_calls_with_correct_arguments(mock_data_client):
    mock_data_client.find_draft_services_iter.return_value = iter([])
    framework_helpers.get_submitted_drafts(mock_data_client, 'digital-biscuits-and-cakes', 12345)
    mock_data_client.find_draft_services_iter.assert_called_with(12345, framework='digital-biscuits-and-cakes')


def test_get_submitted_drafts_returns_submitted_draft_services_only(mock_data_client):
    mock_data_client.find_draft_services_iter.return_value = iter((
        {"id": 123, "status": "submitted"},
        {"id": 234, "status": "failed"},
        {"id": 345, "status": "submitted"},
        {"id": 456, "status": "draft"},
    ))
    result = framework_helpers.get_submitted_drafts(mock_data_client, 12345, 'digital-biscuits-and-cakes')
    assert result == (
        {"id": 123, "status": "submitted"},
        {"id": 345, "status": "submitted"},
    )


def test_get_submitted_drafts_returns_submitted_draft_services_even_with_service_ids(mock_data_client):
    mock_data_client.find_draft_services_iter.return_value = iter((
        {"id": 1, "status": "not-submitted"},
        {"id": 2, "status": "submitted", "serviceId": "ALREADY_A_LIVE_SERVICE"},
        {"id": 3, "status": "submitted"},
    ))
    result = framework_helpers.get_submitted_drafts(mock_data_client, 12345, 'digital-biscuits-and-cakes')
    assert result == (
        {"id": 2, "status": "submitted", "serviceId": "ALREADY_A_LIVE_SERVICE"},
        {"id": 3, "status": "submitted"},
    )


def test_set_framework_result_calls_with_correct_arguments(mock_data_client):
    assert framework_helpers.set_framework_result(mock_data_client, 'g-whizz-6', 123456, True, 'user') == \
        "  Result set OK: 123456 - PASS"
    assert framework_helpers.set_framework_result(mock_data_client, 'g-slug-2', 567890, False, 'script-user') == \
        "  Result set OK: 567890 - FAIL"
    mock_data_client.set_framework_result.assert_has_calls([
        call(123456, 'g-whizz-6', True, 'user'),
        call(567890, 'g-slug-2', False, 'script-user'),
    ])


def test_set_framework_result_returns_error_message_if_update_fails(mock_data_client):
    mock_data_client.set_framework_result.side_effect = [HTTPError(), HTTPError(Mock(status_code=400))]
    assert framework_helpers.set_framework_result(mock_data_client, 'g-whizz-6', 123456, True, 'user') == \
        "  Error inserting result for 123456 (True): Unknown request failure in dmapiclient (status: 503)"
    assert framework_helpers.set_framework_result(mock_data_client, 'digital-stuff', 567890, False, 'script-user') == \
        "  Error inserting result for 567890 (False): Unknown request failure in dmapiclient (status: 400)"


def test_has_supplier_submitted_services_with_no_submitted_services(mock_data_client):
    mock_data_client.find_draft_services_iter.return_value = [
        {"id": 234, "status": "failed"},
        {"id": 456, "status": "not-submitted"}
    ]
    assert framework_helpers.has_supplier_submitted_services(mock_data_client, 'g-spot-7', 567890) is False


def test_has_supplier_submitted_services_with_submitted_services(mock_data_client):
    mock_data_client.find_draft_services_iter.return_value = [
        {"id": 234, "status": "submitted"},
        {"id": 456, "status": "not-submitted"}
    ]
    assert framework_helpers.has_supplier_submitted_services(mock_data_client, 'g-spot-7', 567890) is True


def test_find_suppliers_on_framework(mock_data_client):
    mock_data_client.find_framework_suppliers.return_value = {
        'extraneous_field': 'foo',
        'supplierFrameworks': [
            {'supplierId': 123, 'onFramework': True},
            {'supplierId': 234, 'onFramework': False},
            {'supplierId': 345, 'onFramework': False},
            {'supplierId': 456, 'onFramework': True},
        ]
    }

    assert list(framework_helpers.find_suppliers_on_framework(mock_data_client, 'framework-slug')) == [
        {'supplierId': 123, 'onFramework': True},
        {'supplierId': 456, 'onFramework': True},
    ]


def test_find_suppliers_with_details_and_draft_services(mock_data_client):
    mock_data_client.get_interested_suppliers.return_value = {
        'interestedSuppliers': [4, 3, 2]
    }
    mock_data_client.get_supplier.side_effect = lambda id: {'suppliers': 'supplier {}'.format(id)}

    mock_data_client.get_supplier_framework_info.side_effect = lambda *args: {
        (4, 'framework-slug'): {
            'frameworkInterest': {
                'declaration': {'status': 'complete'},
                'onFramework': True,
                'countersignedPath': None,
                'countersignedAt': None,
            }
        },
        (3, 'framework-slug'): {
            'frameworkInterest': {
                'declaration': {'status': 'started'},
                'onFramework': False,
                'countersignedPath': None,
                'countersignedAt': None,
            }
        },
        (2, 'framework-slug'): {
            'frameworkInterest': {
                'declaration': {'status': 'complete'},
                'onFramework': True,
                'countersignedPath': 'some/path',
                'countersignedAt': '2017-01-02T03:04:05.000006Z',
            }
        },
    }[args]

    mock_data_client.find_draft_services.return_value = {
        "services": [
            {'status': 'submitted', 'lotSlug': 'saas'},
            {'status': 'submitted', 'lotSlug': 'saas'},
            {'status': 'submitted', 'lotSlug': 'saas'},
            {'status': 'submitted', 'lotSlug': 'paas'},
            {'status': 'failed', 'lotSlug': 'iaas'},
            {'status': 'not-submitted', 'lotSlug': 'saas'},
            {'status': 'not-submitted', 'lotSlug': 'paas'},
            {'status': 'not-submitted', 'lotSlug': 'paas'},
        ]
    }

    records = framework_helpers.find_suppliers_with_details_and_draft_services(mock_data_client, 'framework-slug')
    # Ordering of records is not guaranteed so compare individually
    records = list(records)
    assert len(records) == 3
    for record in records:
        assert record in [
            {
                'supplier': 'supplier 4',
                'supplier_id': 4,
                'services': [
                    {'status': 'submitted', 'lotSlug': 'saas'},
                    {'status': 'submitted', 'lotSlug': 'saas'},
                    {'status': 'submitted', 'lotSlug': 'saas'},
                    {'status': 'submitted', 'lotSlug': 'paas'},
                    {'status': 'failed', 'lotSlug': 'iaas'},
                    {'status': 'not-submitted', 'lotSlug': 'saas'},
                    {'status': 'not-submitted', 'lotSlug': 'paas'},
                    {'status': 'not-submitted', 'lotSlug': 'paas'}
                ],
                'declaration': {'status': 'complete'},
                'countersignedPath': '',
                'countersignedAt': '',
                'onFramework': True
            },
            {
                'supplier': 'supplier 3',
                'supplier_id': 3,
                'services': [
                    {'status': 'submitted', 'lotSlug': 'saas'},
                    {'status': 'submitted', 'lotSlug': 'saas'},
                    {'status': 'submitted', 'lotSlug': 'saas'},
                    {'status': 'submitted', 'lotSlug': 'paas'},
                    {'status': 'failed', 'lotSlug': 'iaas'},
                    {'status': 'not-submitted', 'lotSlug': 'saas'},
                    {'status': 'not-submitted', 'lotSlug': 'paas'},
                    {'status': 'not-submitted', 'lotSlug': 'paas'}
                ],
                'declaration': {'status': 'started'},
                'countersignedPath': '',
                'countersignedAt': '',
                'onFramework': False
            },
            {
                'supplier': 'supplier 2',
                'supplier_id': 2,
                'services': [
                    {'status': 'submitted', 'lotSlug': 'saas'},
                    {'status': 'submitted', 'lotSlug': 'saas'},
                    {'status': 'submitted', 'lotSlug': 'saas'},
                    {'status': 'submitted', 'lotSlug': 'paas'},
                    {'status': 'failed', 'lotSlug': 'iaas'},
                    {'status': 'not-submitted', 'lotSlug': 'saas'},
                    {'status': 'not-submitted', 'lotSlug': 'paas'},
                    {'status': 'not-submitted', 'lotSlug': 'paas'}
                ],
                'declaration': {'status': 'complete'},
                'countersignedPath': 'some/path',
                'countersignedAt': '2017-01-02T03:04:05.000006Z',
                'onFramework': True}
        ]


def test_find_suppliers_with_details_and_draft_service_counts(mock_data_client):
    mock_data_client.get_interested_suppliers.return_value = {
        'interestedSuppliers': [4, 3, 2]
    }
    mock_data_client.get_supplier.side_effect = lambda id: {'suppliers': {'id': id, 'name': 'supplier {}'.format(id)}}

    mock_data_client.get_supplier_framework_info.side_effect = lambda *args: {
        (4, 'framework-slug'): {
            'frameworkInterest': {
                'declaration': {'status': 'complete'},
                'onFramework': True,
                'countersignedPath': None,
                'countersignedAt': None,
            }
        },
        (3, 'framework-slug'): {
            'frameworkInterest': {
                'declaration': {'status': 'started'},
                'onFramework': False,
                'countersignedPath': None,
                'countersignedAt': None,
            }
        },
        (2, 'framework-slug'): {
            'frameworkInterest': {
                'declaration': {'status': 'complete'},
                'onFramework': True,
                'countersignedPath': 'some/path',
                'countersignedAt': '2017-01-02T03:04:05.000006Z',
            }
        },
    }[args]

    mock_data_client.find_draft_services_iter.return_value = [
        {'status': 'submitted', 'lotSlug': 'saas'},
        {'status': 'submitted', 'lotSlug': 'saas'},
        {'status': 'submitted', 'lotSlug': 'saas'},
        {'status': 'submitted', 'lotSlug': 'paas'},
        {'status': 'failed', 'lotSlug': 'iaas'},
        {'status': 'not-submitted', 'lotSlug': 'saas'},
        {'status': 'not-submitted', 'lotSlug': 'paas'},
        {'status': 'not-submitted', 'lotSlug': 'paas'},
    ]

    records = framework_helpers.find_suppliers_with_details_and_draft_service_counts(mock_data_client, 'framework-slug')
    records = list(records)
    assert records == [
        {
            'supplier': {'id': 4, 'name': 'supplier 4'},
            'supplier_id': 4,
            'declaration': {'status': 'complete'},
            'countersignedPath': '',
            'counts': Counter(
                {
                    ('saas', 'submitted'): 3,
                    ('paas', 'not-submitted'): 2,
                    ('paas', 'submitted'): 1,
                    ('iaas', 'failed'): 1,
                    ('saas', 'not-submitted'): 1}
            ),
            'countersignedAt': '',
            'onFramework': True
        },
        {
            'supplier': {'id': 3, 'name': 'supplier 3'},
            'supplier_id': 3,
            'declaration': {'status': 'started'},
            'countersignedPath': '',
            'counts': Counter(
                {
                    ('saas', 'submitted'): 3,
                    ('paas', 'not-submitted'): 2,
                    ('paas', 'submitted'): 1,
                    ('iaas', 'failed'): 1,
                    ('saas', 'not-submitted'): 1}
            ),
            'countersignedAt': '',
            'onFramework': False
        },
        {
            'supplier': {'id': 2, 'name': 'supplier 2'},
            'supplier_id': 2,
            'declaration': {'status': 'complete'},
            'countersignedPath': 'some/path',
            'counts': Counter(
                {
                    ('saas', 'submitted'): 3,
                    ('paas', 'not-submitted'): 2,
                    ('paas', 'submitted'): 1,
                    ('iaas', 'failed'): 1,
                    ('saas', 'not-submitted'): 1}
            ),
            'countersignedAt': '2017-01-02T03:04:05.000006Z',
            'onFramework': True
        }
    ]


def test_find_suppliers(mock_data_client):
    mock_data_client.get_interested_suppliers.return_value = {
        'interestedSuppliers': [4, 3, 2]
    }
    records = list(framework_helpers.find_suppliers(mock_data_client, 'framework-slug'))

    mock_data_client.get_interested_suppliers.assert_has_calls([
        call('framework-slug')
    ])
    assert records == [
        {'supplier_id': 4}, {'supplier_id': 3}, {'supplier_id': 2}
    ]


def test_find_suppliers_filtered_by_ids(mock_data_client):
    mock_data_client.get_interested_suppliers.return_value = {
        'interestedSuppliers': [4, 3, 2]
    }

    records = list(framework_helpers.find_suppliers(mock_data_client, 'framework-slug', supplier_ids=[2, 4]))

    assert records == [
        {'supplier_id': 4}, {'supplier_id': 2},
    ]


@pytest.mark.parametrize("supplier_id", (1, 2,))
def test_add_supplier_info(mock_data_client, supplier_id):
    mock_data_client.get_supplier.return_value = {'suppliers': 'supplier {}'.format(supplier_id)}

    record = framework_helpers.add_supplier_info(mock_data_client, {'supplier_id': supplier_id, 'foo': 'bar'})

    assert mock_data_client.get_supplier.call_args == ((supplier_id,),)
    assert record == {'supplier_id': supplier_id, 'foo': 'bar', 'supplier': 'supplier {}'.format(supplier_id)}


@pytest.mark.parametrize("on_framework", (False, True,))
def test_add_framework_info(mock_data_client, on_framework):
    mock_data_client.get_supplier_framework_info.return_value = {
        'frameworkInterest': {
            'declaration': {'status': 'complete'},
            'onFramework': on_framework,
            'countersignedPath': None,
            'countersignedAt': None,
        }
    }

    record = framework_helpers.add_framework_info(mock_data_client, 'g-things-23', {'supplier_id': 123, 'foo': 'bar'})

    assert mock_data_client.get_supplier_framework_info.call_args == ((123, 'g-things-23',),)
    assert record == {
        'supplier_id': 123,
        'foo': 'bar',
        'onFramework': on_framework,
        'declaration': {
            'status': 'complete',
        },
        'countersignedPath': '',
        'countersignedAt': '',
    }


def test_add_framework_info_fails_on_non_404_error(mock_data_client):
    mock_data_client.get_supplier_framework_info.side_effect = HTTPError(Mock(status_code=400))

    with pytest.raises(HTTPError):
        framework_helpers.add_framework_info(mock_data_client, 'framework-slug', {'supplier_id': 123, 'foo': 'bar'})


def test_add_draft_counts(mock_data_client):
    mock_data_client.find_draft_services_iter.return_value = [
        {'status': 'submitted', 'lotSlug': 'saas'},
        {'status': 'submitted', 'lotSlug': 'saas'},
        {'status': 'submitted', 'lotSlug': 'saas'},
        {'status': 'submitted', 'lotSlug': 'paas'},
        {'status': 'failed', 'lotSlug': 'iaas'},
        {'status': 'not-submitted', 'lotSlug': 'saas'},
        {'status': 'not-submitted', 'lotSlug': 'paas'},
        {'status': 'not-submitted', 'lotSlug': 'paas'},
    ]

    record = framework_helpers.add_draft_counts(
        mock_data_client,
        'g-things-23',
        {'supplier': {'id': 123}},
    )
    assert record['counts'] == {
        ("iaas", "failed"): 1,
        ('paas', 'not-submitted'): 2,
        ("paas", "submitted"): 1,
        ("saas", "not-submitted"): 1,
        ("saas", "submitted"): 3,
    }


def test_add_draft_services(mock_data_client):
    mock_data_client.find_draft_services.return_value = {"services": ["service1", "service2"]}

    result = framework_helpers.add_draft_services(
        mock_data_client,
        'framework-slug',
        {'supplier_id': 123}
    )

    mock_data_client.find_draft_services.assert_has_calls([
        call(123, framework='framework-slug'),
    ])
    assert result == {"supplier_id": 123, "services": ["service1", "service2"]}


def test_add_draft_services_filtered_by_lot(mock_data_client):
    mock_data_client.find_draft_services.return_value = {
        "services": [
            {"id": 1, "lotSlug": "good"},
            {"id": 2, "lotSlug": "bad"}
        ]
    }
    result = framework_helpers.add_draft_services(
        mock_data_client,
        "framework-slug",
        {'supplier_id': 123},
        lot="good"
    )
    assert result == {
        "supplier_id": 123,
        "services": [
            {"id": 1, "lotSlug": "good"},
        ]
    }
    mock_data_client.find_draft_services.assert_has_calls([
        call(123, framework='framework-slug'),
    ])


def test_add_draft_services_filtered_by_status(mock_data_client):
    mock_data_client.find_draft_services.return_value = {
        "services": [
            {"id": 1, "status": "submitted"},
            {"id": 2, "status": "failed"}
        ]
    }
    result = framework_helpers.add_draft_services(
        mock_data_client,
        "framework-slug",
        {'supplier_id': 123},
        statuses=["submitted"]
    )
    assert result == {
        "supplier_id": 123,
        "services": [
            {"id": 1, "status": "submitted"},
        ]
    }
    mock_data_client.find_draft_services.assert_has_calls([
        call(123, framework='framework-slug'),
    ])
