import pytest
import six
from mock import Mock, call, patch, ANY, mock_open

from dmscripts import export_g8_suppliers
from dmapiclient import HTTPError
from dmutils.content_loader import ContentQuestion


def test_find_suppliers_produces_results_with_supplier_ids(mock_data_client):
    mock_data_client.get_interested_suppliers.return_value = {
        'interestedSuppliers': [4, 3, 2]
    }

    records = list(export_g8_suppliers.find_suppliers(mock_data_client, 'framework-slug'))

    mock_data_client.get_interested_suppliers.assert_has_calls([
        call('framework-slug')
    ])
    assert records == [
        {'supplier_id': 4}, {'supplier_id': 3}, {'supplier_id': 2}
    ]


def test_find_suppliers_filtered_by_supplier_ids(mock_data_client):
    mock_data_client.get_interested_suppliers.return_value = {
        'interestedSuppliers': [4, 3, 2]
    }

    records = list(export_g8_suppliers.find_suppliers(mock_data_client, 'framework-slug', supplier_ids=[2, 4]))

    assert records == [
        {'supplier_id': 4}, {'supplier_id': 2},
    ]


def test_add_supplier_info(mock_data_client):
    mock_data_client.get_supplier.side_effect = [
        {'suppliers': 'supplier 1'},
        {'suppliers': 'supplier 2'},
    ]

    supplier_info_adder = export_g8_suppliers.add_supplier_info(mock_data_client)
    records = [
        supplier_info_adder({'supplier_id': 1}),
        supplier_info_adder({'supplier_id': 2}),
    ]

    mock_data_client.get_supplier.assert_has_calls([
        call(1), call(2)
    ])
    assert records == [
        {'supplier_id': 1, 'supplier': 'supplier 1'},
        {'supplier_id': 2, 'supplier': 'supplier 2'},
    ]


def test_add_draft_services(mock_data_client):
    mock_data_client.find_draft_services.side_effect = [
        {"services": ["service1", "service2"]},
        {"services": ["service3", "service4"]},
    ]

    service_adder = export_g8_suppliers.add_draft_services(mock_data_client, 'framework-slug')
    in_records = [
        {"supplier_id": 1},
        {"supplier_id": 2},
    ]
    out_records = list(map(service_adder, in_records))

    mock_data_client.find_draft_services.assert_has_calls([
        call(1, framework='framework-slug'),
        call(2, framework='framework-slug'),
    ])
    assert out_records == [
        {"supplier_id": 1, "services": ["service1", "service2"]},
        {"supplier_id": 2, "services": ["service3", "service4"]},
    ]


def test_add_draft_services_filtered_by_lot(mock_data_client):
    mock_data_client.find_draft_services.return_value = {
        "services": [
            {"lotSlug": "good"},
            {"lotSlug": "bad"}
        ]
    }
    service_adder = export_g8_suppliers.add_draft_services(
        mock_data_client, "framework-slug",
        lot="good")
    assert service_adder({"supplier_id": 1}) == {
        "supplier_id": 1,
        "services": [
            {"lotSlug": "good"},
        ]
    }
    mock_data_client.find_draft_services.assert_has_calls([
        call(1, framework='framework-slug'),
    ])


def test_add_draft_services_filtered_by_status(mock_data_client):
    mock_data_client.find_draft_services.return_value = {
        "services": [
            {"status": "submitted"},
            {"status": "failed"}
        ]
    }
    service_adder = export_g8_suppliers.add_draft_services(
        mock_data_client, "framework-slug",
        status="submitted")
    assert service_adder({"supplier_id": 1}) == {
        "supplier_id": 1,
        "services": [
            {"status": "submitted"},
        ]
    }
    mock_data_client.find_draft_services.assert_has_calls([
        call(1, framework='framework-slug'),
    ])


@pytest.mark.parametrize('record,count', [
    ({"services": [
        {"theId": ["Label", "other"]},
        {"theId": ["other"]},
        {"theId": ["Label"]},
    ]}, 2),
    ({"services": []}, 0),
    ({"services": [{}]}, 0),
])
def test_count_field_in_record(record, count):
    assert export_g8_suppliers.count_field_in_record("theId", "Label", record) == count


def test_make_fields_from_content_question():
    questions = [
        ContentQuestion({"id": "check1",
                         "type": "checkboxes",
                         "options": [
                             {"label": "Option 1"},
                             {"label": "Option 2"},
                         ]}),
        ContentQuestion({"id": "custom",
                         "type": "custom",
                         "fields": {
                             "field1": "field1",
                             "field2": "field2",
                         }}),
        ContentQuestion({"id": "basic",
                         "type": "boolean"}),
    ]
    record = {
        "services": [
            {"check1": ["Option 1"],
             "field1": "Blah",
             "field2": "Foo",
             "basic": False},
            {"check1": ["Option 1", "Option 2"],
             "field1": "Foo",
             "basic": True},
        ]
    }
    assert export_g8_suppliers.make_fields_from_content_questions(questions, record) == [
        ("check1 Option 1", 2),
        ("check1 Option 2", 1),
        ("field1", "Blah|Foo"),
        ("field2", "Foo|"),
        ("basic", "False|True"),
    ]


def test_add_framework_info(mock_data_client):
    mock_data_client.get_supplier_framework_info.side_effect = [
        {'frameworkInterest': {'declaration': {'status': 'complete'}, 'onFramework': True}},
        {'frameworkInterest': {'declaration': {'status': 'complete'}, 'onFramework': False}},
    ]

    framework_info_adder = export_g8_suppliers.add_framework_info(mock_data_client, 'framework-slug')
    records = [
        framework_info_adder({'supplier_id': 1}),
        framework_info_adder({'supplier_id': 2}),
    ]

    mock_data_client.get_supplier_framework_info.assert_has_calls([
        call(1, 'framework-slug'), call(2, 'framework-slug')
    ])
    assert records == [
        {'supplier_id': 1, 'declaration': {'status': 'complete'}, 'onFramework': True},
        {'supplier_id': 2, 'declaration': {'status': 'complete'}, 'onFramework': False},
    ]


def test_add_framework_info_fails_on_non_404_error(mock_data_client):
    mock_data_client.get_supplier_framework_info.side_effect = HTTPError(Mock(status_code=400))

    framework_info_adder = export_g8_suppliers.add_framework_info(mock_data_client, 'framework-slug')

    with pytest.raises(HTTPError):
        framework_info_adder({'supplier_id': 1})


def test_add_framework_info_fails_if_incomplete_declaration_is_not_failed(mock_data_client):
    mock_data_client.get_supplier_framework_info.return_value = {
        'frameworkInterest': {'declaration': {'status': 'incomplete'}, 'onFramework': None}
    }

    framework_info_adder = export_g8_suppliers.add_framework_info(mock_data_client, 'framework-slug')

    with pytest.raises(AssertionError):
        framework_info_adder({'supplier_id': 1})


def test_add_draft_counts(mock_data_client):
    mock_data_client.find_draft_services_iter.return_value = [
        {'status': 'submitted', 'lot': 'saas'},
        {'status': 'submitted', 'lot': 'saas'},
        {'status': 'submitted', 'lot': 'paas'},
        {'status': 'not-submitted', 'lot': 'saas'},
        {'status': 'not-submitted', 'lot': 'paas'},
        {'status': 'not-submitted', 'lot': 'paas'},
        {'status': 'not-submitted', 'lot': 'paas'},
        {'status': 'published', 'lot': 'scs'},  # anything not submitted or failed is considered draft
    ]

    draft_counts_adder = export_g8_suppliers.add_draft_counts(mock_data_client, 'framework-slug')

    record = draft_counts_adder({'supplier': {'id': 1}})
    print("COUNTS: {}".format(record['counts']))
    assert record['counts'] == {
        'completed': {
            'saas': 2, 'paas': 1,
            'iaas': 0, 'scs': 0,
        },
        'draft': {
            'saas': 1, 'paas': 3,
            'iaas': 0, 'scs': 1,
        },
    }


def test_get_declaration_questions():
    q1, q2, q3 = Mock(id='found1'), Mock(id='not_found'), Mock(id='found2')

    questions1 = [q1, q2]
    questions2 = [q3]
    sections = [Mock(questions=questions1), Mock(questions=questions2)]
    record = {'declaration': {'found1': 'value1', 'found2': 'value2', 'extra': 'value3'}}

    answers = list(export_g8_suppliers.get_declaration_questions(sections, record))

    assert answers == [
        (q1, 'value1'),
        (q2, None),
        (q3, 'value2'),
    ]


@patch('dmscripts.export_g8_suppliers.get_declaration_questions')
def test_add_failed_question_mandatory_false_is_true(get_declaration_questions):
    get_declaration_questions.return_value = [
        (Mock(id='termsAndConditions', number=1), False)
    ]

    failed_questions_adder = export_g8_suppliers.add_failed_questions(None)

    record = failed_questions_adder({'declaration': {'status': 'complete'}})
    assert record['failed_mandatory'] == ['Q1 - termsAndConditions']


@patch('dmscripts.export_g8_suppliers.get_declaration_questions')
def test_add_failed_question_mandatory_true_is_false(get_declaration_questions):
    get_declaration_questions.return_value = [
        (Mock(id='terrorism', number=17), True)
    ]

    failed_questions_adder = export_g8_suppliers.add_failed_questions(None)

    record = failed_questions_adder({'declaration': {'status': 'complete'}})

    assert record['failed_mandatory'] == ['Q17 - terrorism']


@patch('dmscripts.export_g8_suppliers.get_declaration_questions')
def test_add_failed_question_yes_or_na(get_declaration_questions):
    get_declaration_questions.return_value = [
        (Mock(id='employersInsurance', number=14), "Invalid")
    ]

    failed_questions_adder = export_g8_suppliers.add_failed_questions(None)

    record = failed_questions_adder({'declaration': {'status': 'complete'}})

    assert record['failed_mandatory'] == ['Q14 - employersInsurance']


def test_add_failed_questions_incomplete_declaration():
    failed_questions_adder = export_g8_suppliers.add_failed_questions(None)

    record = failed_questions_adder({'declaration': {'status': 'started'}})

    assert record['failed_mandatory'] == ['INCOMPLETE']
    assert record['discretionary'] == []


def test_service_counts(mock_data_client):
    # Count services
    mock_data_client.find_draft_services_iter.return_value = [
        {'status': 'submitted', 'lot': 'saas'},
        {'status': 'submitted', 'lot': 'saas'},
        {'status': 'submitted', 'lot': 'paas'},
        {'status': 'not-submitted', 'lot': 'scs'},
        {'status': 'not-submitted', 'lot': 'scs'},
        {'status': 'not-submitted', 'lot': 'paas'},
        {'status': 'not-submitted', 'lot': 'paas'},
        {'status': 'published', 'lot': 'paas'},  # anything not submitted or failed is considered draft
    ]
    draft_counts_adder = export_g8_suppliers.add_draft_counts(mock_data_client, 'framework-slug')

    record = draft_counts_adder({'supplier': {'id': 1}})

    counts = export_g8_suppliers.service_counts(record)

    assert counts == [
        ('completed_saas', 2),
        ('completed_paas', 1),
        ('completed_iaas', 0),
        ('completed_scs', 0),
        ('draft_saas', 0),
        ('draft_paas', 3),
        ('draft_iaas', 0),
        ('draft_scs', 2),
    ]

SUCCESSFUL_RECORD = {
    'onFramework': True,
    'supplier': {'id': 1,
                 'name': 'Bluedice Ideas Limited'},
    'declaration': {'nameOfOrganisation': 'Young Money Franchise LTD',
                    'primaryContact': 'Yolo Swaggins',
                    'primaryContactEmail': 'yolo.swaggins@example.com',
                    'tradingNames': 'Old Money Franchise',
                    'registeredAddress': 'The house on the street',
                    'companyNumber': '009900',
                    'currentRegisteredCountry': 'France'},
    'counts': {
        'completed': {
            'saas': 2, 'paas': 1,
            'iaas': 0, 'scs': 0,
        },
        'failed': {
            'saas': 2, 'paas': 0,
            'iaas': 0, 'scs': 0,
        },
        'draft': {
            'saas': 0, 'paas': 3,
            'iaas': 0, 'scs': 0,
        },
    }
}
FAILED_RECORD = {
    'onFramework': False,
    'supplier': {'id': 1,
                 'name': 'Bluedice Ideas Limited'},
    'declaration': {'nameOfOrganisation': 'Young Money Franchise LTD',
                    'primaryContact': 'Yolo Swaggins',
                    'primaryContactEmail': 'yolo.swaggins@example.com',
                    'tradingNames': 'Old Money Franchise',
                    'registeredAddress': 'The house on the street',
                    'companyNumber': '009900',
                    'currentRegisteredCountry': 'France'},
    'failed_mandatory': ['Q1', 'Q3', 'Q5'],
    'discretionary': [],
    'counts': {
        'completed': {
            'saas': 2, 'paas': 1,
            'iaas': 0, 'scs': 0,
        },
        'failed': {
            'saas': 2, 'paas': 0,
            'iaas': 0, 'scs': 0,
        },
        'draft': {
            'saas': 0, 'paas': 3,
            'iaas': 0, 'scs': 0,
        },
    }
}
DISCRETIONARY_RECORD = {
    'onFramework': None,
    'supplier': {'id': 1,
                 'name': 'Bluedice Ideas Limited'},
    'declaration': {'nameOfOrganisation': 'Young Money Franchise LTD',
                    'primaryContact': 'Yolo Swaggins',
                    'primaryContactEmail': 'yolo.swaggins@example.com',
                    'tradingNames': 'Old Money Franchise',
                    'registeredAddress': 'The house on the street',
                    'companyNumber': '009900',
                    'currentRegisteredCountry': 'France'},
    'failed_mandatory': [],
    'discretionary': [
        ('Q21', 'val1'),
        ('Q22', 'val2'),
        ('Q23', 'val3'),
    ],
    'counts': {
        'completed': {
            'saas': 2, 'paas': 1,
            'iaas': 0, 'scs': 0,
        },
        'failed': {
            'saas': 2, 'paas': 0,
            'iaas': 0, 'scs': 0,
        },
        'draft': {
            'saas': 0, 'paas': 3,
            'iaas': 0, 'scs': 0,
        },
    }
}


def test_write_to_csv():
    # mock_open mocks the open function
    # if we want to mock multiple files we want the configured MagicMock that mock_open returns
    successful_file = mock_open()()
    failed_file = mock_open()()
    discretionary_file = mock_open()()
    all_files = [successful_file, failed_file, discretionary_file]

    with patch.object(six.moves.builtins, 'open', side_effect=all_files) as mocked_open:
        handlers = [
            export_g8_suppliers.SuccessfulHandler(),
            export_g8_suppliers.FailedHandler(),
            export_g8_suppliers.DiscretionaryHandler()
        ]

        with export_g8_suppliers.MultiCSVWriter('example', handlers) as writer:
            mocked_open.assert_has_calls([
                call('example/successful.csv', ANY),
                call('example/failed.csv', ANY),
                call('example/discretionary.csv', ANY),
            ])

            writer.write_row(SUCCESSFUL_RECORD)
            writer.write_row(FAILED_RECORD)
            writer.write_row(DISCRETIONARY_RECORD)

            successful_file.write.assert_has_calls([
                call('supplier_name,supplier_id,contact_name,contact_email\r\n'),
                call('Bluedice Ideas Limited,1,Yolo Swaggins,yolo.swaggins@example.com\r\n'),
            ])
            failed_file.write.assert_has_calls([
                call('supplier_name,supplier_id,failed_mandatory,contact_name,contact_email\r\n'),
                call('Bluedice Ideas Limited,1,"Q1,Q3,Q5",Yolo Swaggins,yolo.swaggins@example.com\r\n'),
            ])
            discretionary_file.write.assert_has_calls([
                call('supplier_name,supplier_id,Q21,Q22,Q23,contact_name,contact_email\r\n'),
                call('Bluedice Ideas Limited,1,val1,val2,val3,Yolo Swaggins,yolo.swaggins@example.com\r\n'),
            ])
