from dmscripts.export_dos_labs import append_contact_information_to_services


def test_append_contact_information_to_services():
    records = [
        {
            'services': [{'serviceName': 'service1'}, {'serviceName': 'service2'}],
            'supplier': {'contactInformation': [{'email': 'me@me.com', 'phone': '1234', 'other': 'value'}]}
        },
        {
            'services': [{'serviceName': 'service3'}],
            'supplier': {'contactInformation': [{'email': 'me2@me2.com', 'phone': '56789', 'other': 'value'}]}
        },
    ]

    res = append_contact_information_to_services(records, ['email', 'phone'])

    assert res == [
        {
            'services': [
                {'serviceName': 'service1', 'email': 'me@me.com', 'phone': '1234'},
                {'serviceName': 'service2', 'email': 'me@me.com', 'phone': '1234'},
            ],
            'supplier': {'contactInformation': [{'email': 'me@me.com', 'phone': '1234', 'other': 'value'}]}
        },
        {
            'services': [{'serviceName': 'service3', 'email': 'me2@me2.com', 'phone': '56789'}],
            'supplier': {'contactInformation': [{'email': 'me2@me2.com', 'phone': '56789', 'other': 'value'}]}
        },
    ]
