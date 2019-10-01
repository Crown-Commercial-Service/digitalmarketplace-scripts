import pytest

import dmscripts.helpers.csv_helpers as csv_helpers
from dmcontent.content_loader import ContentLoader


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
    assert csv_helpers.count_field_in_record("theId", "Label", record) == count


def test_read_csv():
    assert csv_helpers.read_csv('tests/fixtures/framework_results.csv') == [
        ['123', 'Supplier Name', 'pass'],
        ['234', 'Supplier Name', 'fail'],
        ['345', 'Supplier Name', ' PASS'],
        ['456', 'Supplier Name', ' FAIL'],
        ['567', 'Supplier Name', ' Yes'],
        ['Company Name', 'Supplier Name', 'pass'],
        ['678', 'Supplier Name', 'PasS'],
    ]


class TestMakeFieldsFromContentQuestions:

    def setup(self):
        content_loader = ContentLoader('tests/fixtures/content')
        content_loader.load_manifest('dos', "services", "edit_submission")
        self.content_manifest = content_loader.get_manifest('dos', "edit_submission")

        self.record = {
            "supplier": {
                "name": "ACME INC"
            },
            "declaration": {
                "supplierRegisteredName": "ACME Ltd"
            },
            "supplier_id": 34567,
            "onFramework": True,
            "services": [
                {
                    "locations": [
                        "Offsite",
                        "Scotland",
                        "North East England"
                    ],
                    "accessibleApplicationsOutcomes": True
                }
            ]
        }

    def test_make_fields_from_content_questions_with_checkbox_questions(self):
        locations_question = self.content_manifest.get_question("locations")
        assert csv_helpers.make_fields_from_content_questions([locations_question], self.record) == [
            ('locations Offsite', 1),
            ('locations Scotland', 1),
            ('locations North East England', 1),
            ('locations North West England', 0),
            ('locations Yorkshire and the Humber', 0),
            ('locations East Midlands', 0),
            ('locations West Midlands', 0),
            ('locations East of England', 0),
            ('locations Wales', 0),
            ('locations London', 0),
            ('locations South East England', 0),
            ('locations South West England', 0),
            ('locations Northern Ireland', 0)
        ]

    def test_make_fields_from_content_questions_with_boolean(self):
        locations_question = self.content_manifest.get_question("accessibleApplicationsOutcomes")

        assert csv_helpers.make_fields_from_content_questions([locations_question], self.record) == [
            ('accessibleApplicationsOutcomes', 'True'),
        ]
