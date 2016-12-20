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


@pytest.mark.parametrize("supplier_id", (1, 2,))
def test_add_supplier_info(mock_data_client, supplier_id):
    mock_data_client.get_supplier.return_value = {'suppliers': 'supplier {}'.format(supplier_id)}

    record = export_framework_applicant_details.add_supplier_info(mock_data_client, {'supplier_id': supplier_id})

    assert mock_data_client.get_supplier.call_args == ((supplier_id,),)
    assert record == {'supplier_id': supplier_id, 'supplier': 'supplier {}'.format(supplier_id)}


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

    record = export_framework_applicant_details.add_framework_info(mock_data_client, 'g-cloud-8', {'supplier_id': 1})

    assert mock_data_client.get_supplier_framework_info.call_args == ((1, 'g-cloud-8',),)
    assert record == {
        'supplier_id': 1,
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
        export_framework_applicant_details.add_framework_info(mock_data_client, 'g-cloud-8', {'supplier_id': 1})


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
        mock_data_client,
        'g-cloud-8',
        {'supplier': {'id': 1}},
    )
    assert record['counts'] == {'iaas': 1, 'paas': 1, 'saas': 3}

#
# TODO these tests are not comprehensive enough - fix that. Notably they fail to check the final output of the script
#
