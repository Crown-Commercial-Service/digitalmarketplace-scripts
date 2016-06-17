# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from dmscripts.insert_g8_framework_results import insert_result, get_submitted_drafts, check_declaration_answers, \
    has_supplier_submitted_services, process_g8_results
from mock import mock
from dmapiclient import HTTPError


VALID_COMPLETE_G8_DECLARATION = {
    "termsAndConditions": True,
    "registeredAddressBuilding": "23 Four Street",
    "understandTool": True,
    "distortingCompetition": False,
    "skillsAndResources": True,
    "significantOrPersistentDeficiencies": False,
    "cyberEssentials": False,
    "companyRegistrationNumber": "1234456",
    "dunsNumber": "123123123",
    "registeredVATNumber": "543456543",
    "distortedCompetition": False,
    "conspiracyCorruptionBribery": False,
    "contactNameContractNotice": "A.N. Other",
    "contactEmailContractNotice": "g8-supplier@example.com",
    "organisationSize": "micro",
    "graveProfessionalMisconduct": False,
    "GAAR": False,
    "canProvideCloudServices": True,
    "bankrupt": False,
    "confidentialInformation": False,
    "seriousMisrepresentation": False,
    "understandHowToAskQuestions": True,
    "primaryContactEmail": "g8-supplier@example.com",
    "taxEvasion": False,
    "primaryContact": "Primary Contact",
    "subcontracting": [
        "yourself without the use of third parties (subcontractors)"
    ],
    "tradingStatus": "limited company",
    "terrorism": False,
    "conflictOfInterest": False,
    "proofOfClaims": True,
    "status": "complete",
    "witheldSupportingDocuments": False,
    "registeredAddressTown": "Cardigan",
    "currentRegisteredCountry": "UK",
    "misleadingInformation": False,
    "equalityAndDiversity": True,
    "nameOfOrganisation": "Cardigan Cardigans Ltd",
    "fraudAndTheft": False,
    "firstRegistered": "2001",
    "employersInsurance": "Yes",
    "unspentTaxConvictions": False,
    "establishedInTheUK": True,
    "servicesHaveOrSupport": True,
    "influencedContractingAuthority": False,
    "readUnderstoodGuidance": True,
    "environmentalSocialLabourLaw": False,
    "termsOfParticipation": True,
    "accuratelyDescribed": True,
    "organisedCrime": False,
    "MI": True,
    "cyberEssentialsPlus": False,
    "registeredAddressPostcode": "CD3 4GH",
    "tradingNames": "Cardies'r'Us"
}


def test_insert_result_calls_with_correct_arguments(mock_data_client):
    assert insert_result(mock_data_client, 123456, True, 'user') == '  Result set OK: 123456'
    mock_data_client.set_framework_result.assert_called_with(123456, 'g-cloud-8', True, 'user')


def test_insert_result_returns_error_message_if_update_fails(mock_data_client):
    mock_data_client.set_framework_result.side_effect = HTTPError()
    assert insert_result(mock_data_client, 123456, True, 'user') == \
        '  Error inserting result for 123456 (True): Request failed (status: 503)'


def test_get_submitted_drafts_calls_with_correct_arguments(mock_data_client):
    mock_data_client.find_draft_services.return_value = {'services': []}
    get_submitted_drafts(mock_data_client, 12345)
    mock_data_client.find_draft_services.assert_called_with(12345, framework='g-cloud-8')


def test_get_submitted_drafts_returns_submitted_services_only(mock_data_client):
    mock_data_client.find_draft_services.return_value = {'services': [
                                                        {"id": 1, "status": "not-submitted"},
                                                        {"id": 2, "status": "submitted"}
        ]
    }
    result = get_submitted_drafts(mock_data_client, 12345)
    assert (result == [{"id": 2, "status": "submitted"}])


def test_check_declaration_fails_incomplete_declaration():
    declaration = {"status": "started"}
    assert check_declaration_answers(declaration) == 'Fail'


def test_check_declaration_answers_passes_good_declaration():
    assert check_declaration_answers(VALID_COMPLETE_G8_DECLARATION) == 'Pass'


def test_check_declaration_answers_fails_bad_declaration_true_is_false():
    declaration_content = mock.Mock()
    question_numbers = mock.PropertyMock(side_effect=[1, 17, 21, -1])
    type(declaration_content.get_question.return_value).number = question_numbers
    # Question canProvideCloudServices is incorrectly False so should Fail
    declaration = VALID_COMPLETE_G8_DECLARATION.copy()
    declaration['canProvideCloudServices'] = False
    assert check_declaration_answers(declaration) == 'Fail'


def test_check_declaration_answers_fails_bad_declaration_false_is_true():
    # Question conspiracyCorruptionBribery is incorrectly True so should Fail
    declaration = VALID_COMPLETE_G8_DECLARATION.copy()
    declaration['conspiracyCorruptionBribery'] = True
    assert check_declaration_answers(declaration) == 'Fail'


def test_check_declaration_answers_returns_discretionary_for_false_is_true():
    # Question taxEvasion is incorrectly True so should be Discretionary
    declaration = VALID_COMPLETE_G8_DECLARATION.copy()
    declaration['taxEvasion'] = True
    assert check_declaration_answers(declaration) == 'Discretionary'


def test_check_declaration_answers_passes_good_yes_or_na():
    # Question employersInsurance should pass if 'Yes' or 'Not applicable'
    declaration = VALID_COMPLETE_G8_DECLARATION.copy()
    declaration['employersInsurance'] = "Not applicable"
    assert check_declaration_answers(declaration) == 'Pass'


def test_check_declaration_answers_fails_for_bad_yes_or_na():
    # Question employersInsurance should pass if 'Yes' or 'Not applicable'
    declaration = VALID_COMPLETE_G8_DECLARATION.copy()
    declaration['employersInsurance'] = "No"
    assert check_declaration_answers(declaration) == 'Fail'


def test_has_supplier_submitted_services_for_some_services(mock_data_client):
    mock_data_client.find_draft_services.return_value = {
        "services": [{"status": "submitted"}, {"status": "submitted"}]
    }
    assert has_supplier_submitted_services(mock_data_client, 12345) is True


def test_has_supplier_submitted_services_for_no_services(mock_data_client):
    mock_data_client.find_draft_services.return_value = {
        "services": [{"status": "not-submitted"}]
    }
    assert has_supplier_submitted_services(mock_data_client, 12345) is False


def test_process_g8_results_for_successful(mock_data_client):
    mock_data_client.get_interested_suppliers.return_value = {"interestedSuppliers": [123456]}
    mock_data_client.get_supplier_declaration.return_value = {"declaration": VALID_COMPLETE_G8_DECLARATION}
    mock_data_client.find_draft_services.return_value = {
        "services": [{"status": "submitted"}, {"status": "submitted"}]
    }
    process_g8_results(mock_data_client, 'user')
    mock_data_client.set_framework_result.assert_called_with(123456, 'g-cloud-8', True, 'user')


def test_process_g8_results_for_incomplete_declaration(mock_data_client):
    # Declaration not complete so application should fail
    declaration = VALID_COMPLETE_G8_DECLARATION.copy()
    declaration['status'] = 'started'
    mock_data_client.get_interested_suppliers.return_value = {"interestedSuppliers": [123456]}
    mock_data_client.get_supplier_declaration.return_value = {"declaration": declaration}
    mock_data_client.find_draft_services.return_value = {
        "services": [{"status": "submitted"}, {"status": "submitted"}]
    }
    process_g8_results(mock_data_client, 'user')
    mock_data_client.set_framework_result.assert_called_with(123456, 'g-cloud-8', False, 'user')


def test_process_g8_results_for_discretionary(mock_data_client):
    # Question 'bankrupt' = True is a discretionary fail, so result should be discretionary
    declaration = VALID_COMPLETE_G8_DECLARATION.copy()
    declaration['bankrupt'] = True
    mock_data_client.get_interested_suppliers.return_value = {"interestedSuppliers": [123456]}
    mock_data_client.get_supplier_declaration.return_value = {"declaration": declaration}
    mock_data_client.find_draft_services.return_value = {
        "services": [{"status": "submitted"}, {"status": "submitted"}]
    }
    process_g8_results(mock_data_client, 'user')
    # Discretionary result should not update `supplier_frameworks` at all
    mock_data_client.set_framework_result.assert_not_called()
