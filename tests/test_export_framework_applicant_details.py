import pytest
from mock import Mock, call

from dmscripts import export_framework_applicant_details
from dmapiclient import HTTPError


def test_find_suppliers_produces_results_with_supplier_ids(mock_data_client):
    mock_data_client.get_interested_suppliers.return_value = {
        'interestedSuppliers': [4, 3, 2]
    }

    records = list(export_framework_applicant_details.find_suppliers(mock_data_client, 'g-cloud-8'))

    mock_data_client.get_interested_suppliers.assert_has_calls([
        call('g-cloud-8')
    ])
    assert records == [
        {'supplier_id': 4}, {'supplier_id': 3}, {'supplier_id': 2}
    ]


def test_add_supplier_info(mock_data_client):
    mock_data_client.get_supplier.side_effect = [
        {'suppliers': 'supplier 1'},
        {'suppliers': 'supplier 2'},
    ]

    records = [
        export_framework_applicant_details.add_supplier_info({'supplier_id': 1}, mock_data_client),
        export_framework_applicant_details.add_supplier_info({'supplier_id': 2}, mock_data_client),
    ]

    mock_data_client.get_supplier.assert_has_calls([
        call(1), call(2)
    ])
    assert records == [
        {'supplier_id': 1, 'supplier': 'supplier 1'},
        {'supplier_id': 2, 'supplier': 'supplier 2'},
    ]


def test_add_framework_info(mock_data_client):
    mock_data_client.get_supplier_framework_info.side_effect = [
        {
            'frameworkInterest': {
                'declaration': {'status': 'complete'},
                'onFramework': True,
                'countersignedPath': None,
                'countersignedAt': None
            }
        },
        {
            'frameworkInterest': {
                'declaration': {'status': 'complete'},
                'onFramework': False,
                'countersignedPath': None,
                'countersignedAt': None
            }
        },
    ]

    records = [
        export_framework_applicant_details.add_framework_info({'supplier_id': 1}, mock_data_client, 'g-cloud-8'),
        export_framework_applicant_details.add_framework_info({'supplier_id': 2}, mock_data_client, 'g-cloud-8'),
    ]

    mock_data_client.get_supplier_framework_info.assert_has_calls([
        call(1, 'g-cloud-8'), call(2, 'g-cloud-8')
    ])
    assert records == [
        {'supplier_id': 1, 'onFramework': True, 'declaration': {'status': 'complete'},
         'countersignedPath': '', 'countersignedAt': ''},
        {'supplier_id': 2, 'onFramework': False, 'declaration': {'status': 'complete'},
         'countersignedPath': '', 'countersignedAt': ''}
    ]


def test_add_framework_info_fails_on_non_404_error(mock_data_client):
    mock_data_client.get_supplier_framework_info.side_effect = HTTPError(Mock(status_code=400))

    with pytest.raises(HTTPError):
        export_framework_applicant_details.add_framework_info({'supplier_id': 1}, mock_data_client, 'g-cloud-8')


def test_add_submitted_draft_counts(mock_data_client):
    mock_data_client.find_draft_services_iter.return_value = [
        {'status': 'submitted', 'lot': 'saas'},
        {'status': 'submitted', 'lot': 'saas'},
        {'status': 'submitted', 'lot': 'saas'},
        {'status': 'submitted', 'lot': 'paas'},
        {'status': 'failed', 'lot': 'iaas'},
        {'status': 'not-submitted', 'lot': 'saas'},
        {'status': 'not-submitted', 'lot': 'paas'},
        {'status': 'not-submitted', 'lot': 'paas'},
        {'status': 'published', 'lot': 'paas'},  # anything not submitted or failed is considered draft
    ]

    record = export_framework_applicant_details.add_submitted_draft_counts(
        {'supplier': {'id': 1}},
        mock_data_client,
        'g-cloud-8',
    )
    assert record['counts'] == {'paas': 1, 'saas': 3}
