try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from dmapiclient import HTTPError

from dmscripts.generate_user_email_list_applications import (
    filter_list_of_dicts_by_value,
    get_all_supplier_framework_info,
    find_all_users_given_supplier_frameworks,
    list_users
)


def _return_supplier_framework(supplier_id, on_framework, agreement_returned=None):
    return {
        "frameworkInterest": {
            "agreementReturned": agreement_returned,
            "declaration": "declaration",
            "frameworkSlug": "g-cloud-7",
            "onFramework": on_framework,
            "supplierId": supplier_id
        }
    }


def _return_supplier_framework_passed_application(*args):
    supplier_id = args[0] if args else 1
    return _return_supplier_framework(supplier_id, on_framework=True, agreement_returned=False)


def _return_supplier_framework_failed_application(*args):
    supplier_id = args[0] if args else 1
    return _return_supplier_framework(supplier_id, on_framework=False)


def _return_supplier_framework_no_application(*args):
    supplier_id = args[0] if args else 1
    return _return_supplier_framework(supplier_id, on_framework=None)


def _return_supplier_framework_raises_error(*args):
    raise HTTPError()


def _return_supplier_user(*args, **kwargs):
    supplier_id = kwargs['supplier_id']

    return {
        "users": [{
            "id": supplier_id * 10,
            "emailAddress": "email@email.email",
            "name": "DM Test User",
            "supplier": {
                "name": "DM Test Supplier",
                "supplierId": supplier_id
            }
        }]
    }


def test_filter_list_of_dicts_by_value():
    raw_supplier_frameworks = [
        _return_supplier_framework_passed_application(),
        _return_supplier_framework_failed_application(),
        _return_supplier_framework_no_application(),
    ]
    supplier_frameworks = [
        supplier_framework.get('frameworkInterest') for supplier_framework in raw_supplier_frameworks
        ]
    filtered_supplier_frameworks = filter_list_of_dicts_by_value(supplier_frameworks, 'onFramework', True)

    assert len(filtered_supplier_frameworks) == 1
    assert filtered_supplier_frameworks[0].get('supplierId') == 1
    assert filtered_supplier_frameworks[0].get('onFramework') is True


def test_get_all_supplier_framework_info(mock_data_client):
    # passed application should be fine
    mock_data_client.get_supplier_framework_info.side_effect = _return_supplier_framework_passed_application
    supplier_frameworks = get_all_supplier_framework_info(mock_data_client, 'g-cloud-7', [{'id': 1}])
    assert supplier_frameworks[0].get('agreementReturned') is False
    assert supplier_frameworks[0].get('onFramework') is True

    # failed application should be fine
    mock_data_client.get_supplier_framework_info.side_effect = _return_supplier_framework_failed_application
    supplier_frameworks = get_all_supplier_framework_info(mock_data_client, 'g-cloud-7', [{'id': 1}])
    assert supplier_frameworks[0].get('agreementReturned') is None
    assert supplier_frameworks[0].get('onFramework') is False

    # no application should be filtered out
    mock_data_client.get_supplier_framework_info.side_effect = _return_supplier_framework_no_application
    supplier_frameworks = get_all_supplier_framework_info(mock_data_client, 'g-cloud-7', [{'id': 1}])
    assert supplier_frameworks == []

    # http error shouldn't cause a problem
    mock_data_client.get_supplier_framework_info.side_effect = _return_supplier_framework_raises_error
    supplier_frameworks = get_all_supplier_framework_info(mock_data_client, 'g-cloud-7', [{'id': 1}])
    assert supplier_frameworks == []


def test_find_all_users_given_supplier_frameworks(mock_data_client):
    # assume we have two suppliers, return a list of users
    mock_data_client.find_users.side_effect = _return_supplier_user

    supplier_frameworks = [
        _return_supplier_framework_passed_application(1).get('frameworkInterest'),
        _return_supplier_framework_failed_application(2).get('frameworkInterest'),
    ]
    users = find_all_users_given_supplier_frameworks(mock_data_client, supplier_frameworks)

    assert len(users) == 2
    assert users[0]['supplier']['supplierId'] == 1
    assert users[0]['supplier']['onFramework'] is True

    assert users[1]['supplier']['supplierId'] == 2
    assert users[1]['supplier']['onFramework'] is False


def test_list_users_application_passed(mock_data_client):
    mock_data_client.find_suppliers_iter.return_value = [{"id": 1}]
    mock_data_client.get_supplier_framework_info.side_effect = _return_supplier_framework_passed_application
    mock_data_client.find_users.side_effect = _return_supplier_user

    output = StringIO()
    list_users(mock_data_client, output, 'g-cloud-7')
    assert output.getvalue() == "pass,not returned,email@email.email,DM Test User,1,DM Test Supplier\r\n"


def test_list_users_application_failed(mock_data_client):
    mock_data_client.find_suppliers_iter.return_value = [{"id": 1}]
    mock_data_client.get_supplier_framework_info.side_effect = _return_supplier_framework_failed_application
    mock_data_client.find_users.side_effect = _return_supplier_user

    output = StringIO()
    list_users(mock_data_client, output, 'g-cloud-7')
    assert output.getvalue() == "fail,not returned,email@email.email,DM Test User,1,DM Test Supplier\r\n"


def test_list_users_application_failed_filter_on_framework(mock_data_client):
    mock_data_client.find_suppliers_iter.return_value = [{"id": 1}]
    mock_data_client.get_supplier_framework_info.side_effect = _return_supplier_framework_failed_application
    mock_data_client.find_users.side_effect = _return_supplier_user

    output = StringIO()
    list_users(mock_data_client, output, 'g-cloud-7', on_framework=True)
    assert output.getvalue() == ""


def test_list_users_no_application(mock_data_client):
    mock_data_client.find_suppliers_iter.return_value = [{"id": 1}]
    mock_data_client.get_supplier_framework_info.side_effect = _return_supplier_framework_no_application
    mock_data_client.find_users.side_effect = _return_supplier_user

    output = StringIO()
    list_users(mock_data_client, output, 'g-cloud-7')
    assert output.getvalue() == ""


def test_list_users_no_suppliers(mock_data_client):
    mock_data_client.find_suppliers_iter.return_value = []

    output = StringIO()
    list_users(mock_data_client, output, 'g-cloud-7')
    assert output.getvalue() == ""


def test_list_users_no_users(mock_data_client):
    mock_data_client.find_suppliers_iter.return_value = [{"id": 1}]
    mock_data_client.get_supplier_framework_info.side_effect = _return_supplier_framework_passed_application
    mock_data_client.find_users.return_value = {"users": []}

    output = StringIO()
    list_users(mock_data_client, output, 'g-cloud-7')
    assert output.getvalue() == ""
