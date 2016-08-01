# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict
from dmscripts.insert_dos_framework_results import check_service_essentials, check_declaration_answers, \
    process_submitted_drafts, process_dos_results
from mock import mock


VALID_COMPLETE_DOS_DECLARATION = {
    "10WorkingDays": True,
    "status": "complete",
    "understandTool": True,
    "canProvideFromDayOne": True,
    "distortingCompetition": False,
    "skillsAndResources": True,
    "environmentalSocialLabourLaw": False,
    "cyberEssentials": True,
    "companyRegistrationNumber": "123456789",
    "environmentallyFriendly": True,
    "registeredVATNumber": "987654321",
    "distortedCompetition": False,
    "conspiracyCorruptionBribery": False,
    "contactNameContractNotice": "Someone",
    "serviceStandard": True,
    "contactEmailContractNotice": "dos-supplier@example.com",
    "organisationSize": "micro",
    "graveProfessionalMisconduct": False,
    "accurateInformation": True,
    "unfairCompetition": True,
    "customerSatisfactionProcess": True,
    "GAAR": False,
    "offerServicesYourselves": True,
    "bankrupt": False,
    "continuousProfessionalDevelopment": True,
    "confidentialInformation": False,
    "seriousMisrepresentation": False,
    "licenceOrMemberRequiredDetails": None,
    "consistentDelivery": True,
    "fullAccountability": True,
    "primaryContactEmail": "dos-supplier-primary@example.com",
    "ongoingEngagement": True,
    "mitigatingFactors": None,
    "taxEvasion": False,
    "primaryContact": "Someone else",
    "subcontracting": "yourself without the use of third parties (subcontractors)",
    "significantOrPersistentDeficiencies": False,
    "tradingStatus": "sole trader",
    "terrorism": False,
    "conflictOfInterest": False,
    "proofOfClaims": True,
    "mitigatingFactors2": None,
    "witheldSupportingDocuments": False,
    "requisiteAuthority": True,
    "tradingStatusOther": None,
    "skillsAndCapabilityAssessment": True,
    "termsOfParticipation": True,
    "currentRegisteredCountry": "UK",
    "misleadingInformation": False,
    "termsAndConditions": True,
    "equalityAndDiversity": True,
    "tradingNames": "Great Outcomes Inc.",
    "nameOfOrganisation": "Great Outcomes Ltd",
    "safeguardPersonalData": True,
    "technologyCodesOfPractice": True,
    "evidence": True,
    "transparentContracting": True,
    "safeguardOfficialInformation": True,
    "employersInsurance": "Yes \u2013 your organisation has, or will have in place, employer\u2019s liability "
                          "insurance of at least \u00a35 million and you will provide certification prior to "
                          "framework award.",
    "registeredAddress": "Somewhere, London, SW1A",
    "civilServiceValues": True,
    "unspentTaxConvictions": False,
    "publishContracts": True,
    "establishedInTheUK": True,
    "influencedContractingAuthority": False,
    "appropriateTradeRegistersNumber": None,
    "readUnderstoodGuidance": True,
    "MI": True,
    "firstRegistered": "2001",
    "accuratelyDescribed": True,
    "licenceOrMemberRequired": "none of the above",
    "organisedCrime": False,
    "cyberEssentialsPlus": True,
    "fraudAndTheft": False,
    "informationChanges": True,
    "understandHowToAskQuestions": True
}

COMPLETE_SPECIALISTS_DRAFT = {
    "status": "submitted",
    "bespokeSystemInformation": True,
    "supplierId": 123456,
    "links": {
        "self": "http://api.url/draft-services/62",
        "copy": "http://api.url/draft-services/62/copy",
        "complete": "http://api.url/draft-services/62/complete",
        "publish": "http://api.url/draft-services/62/publish"
    },
    "agileCoachPriceMax": "30",
    "agileCoachPriceMin": "20",
    "openStandardsPrinciples": True,
    "updatedAt": "2016-01-19T11:43:13.779710Z",
    "frameworkSlug": "digital-outcomes-and-specialists",
    "id": 62,
    "frameworkStatus": "open",
    "dataProtocols": True,
    "lotName": "Digital specialists",
    "frameworkName": "Digital Outcomes and Specialists",
    "lot": "digital-specialists",
    "helpGovernmentImproveServices": True,
    "supplierName": "Great Outcomes Inc.",
    "agileCoachLocations": [
        "Scotland"
    ],
    "createdAt": "2016-01-19T09:24:50.157530Z"
}

COMPLETE_OUTCOMES_DRAFT = {
    "status": "submitted",
    "bespokeSystemInformation": True,
    "supplierId": 123456,
    "links": {
        "self": "http://api.url/draft-services/58",
        "copy": "http://api.url/draft-services/58/copy",
        "complete": "http://api.url/draft-services/58/complete",
        "publish": "http://api.url/draft-services/58/publish"
    },
    "helpGovernmentImproveServices": True,
    "openStandardsPrinciples": True,
    "frameworkSlug": "digital-outcomes-and-specialists",
    "supplierName": "Great Outcomes Inc.",
    "frameworkStatus": "open",
    "dataProtocols": True,
    "lotName": "Digital outcomes",
    "frameworkName": "Digital Outcomes and Specialists",
    "lot": "digital-outcomes",
    "updatedAt": "2016-01-19T09:36:27.781699Z",
    "securityTypes": [
        "Firewall audit",
        "Infrastructure review",
        "Threat modelling"
    ],
    "outcomesLocations": [
        "Offsite",
        "Yorkshire and the Humber",
        "East Midlands",
        "Wales"
    ],
    "id": 58,
    "createdAt": "2015-11-30T14:30:44.991173Z"
}

COMPLETE_STUDIOS_DRAFT = {
    "links": {
        "self": "http://api.url/draft-services/61",
        "copy": "http://api.url/draft-services/61/copy",
        "complete": "http://api.url/draft-services/61/complete",
        "publish": "http://api.url/draft-services/61/publish"
    },
    "frameworkSlug": "digital-outcomes-and-specialists",
    "updatedAt": "2016-01-14T12:18:28.795039Z",
    "labAddressTown": "Bexleyheath",
    "id": 61,
    "createdAt": "2015-12-11T12:47:02.693676Z",
    "supplierId": 123456,
    "labWiFi": True,
    "labToilets": False,
    "labAddressPostcode": "BX12 3XY",
    "frameworkStatus": "open",
    "lotName": "User research studios",
    "lot": "user-research-studios",
    "labEyeTracking": "No",
    "status": "submitted",
    "labCarPark": "On-street parking available nearby",
    "labSize": "34",
    "labPublicTransport": "The 123 bus stop is right outside",
    "labDeviceStreaming": "No",
    "labAddressBuilding": "234",
    "labStreaming": "Yes \u2013 included as standard",
    "labHosting": "Yes \u2013 included as standard",
    "serviceName": "Super Labs Inc.",
    "labDesktopStreaming": "Yes \u2013 included as standard",
    "labAccessibility": "There is a ramp to the front door and no steps inside.",
    "labTechAssistance": "Yes \u2013 included as standard",
    "labTimeMin": "2 hours",
    "labWaitingArea": "Yes \u2013 for an additional cost",
    "frameworkName": "Digital Outcomes and Specialists",
    "labViewingArea": "Yes \u2013 included as standard",
    "labBabyChanging": False,
    "supplierName": "Great Outcomes Inc.",
    "labPriceMin": "45"
}

COMPLETE_RESEARCH_PARTICIPANTS_DRAFT = {
    "status": "submitted",
    "manageIncentives": True,
    "recruitLocations": [
        "East Midlands"
    ],
    "links": {
        "self": "http://api.url/draft-services/63",
        "copy": "http://api.url/draft-services/63/copy",
        "complete": "http://api.url/draft-services/63/complete",
        "publish": "http://api.url/draft-services/63/publish"
    },
    "frameworkSlug": "digital-outcomes-and-specialists",
    "supplierId": 123456,
    "recruitFromList": False,
    "frameworkStatus": "open",
    "lotName": "User research participants",
    "frameworkName": "Digital Outcomes and Specialists",
    "recruitMethods": [
        "Initial recruitment offline, but then contact them online"
    ],
    "lot": "user-research-participants",
    "updatedAt": "2016-01-19T13:43:16.820520Z",
    "supplierName": "Great Outcomes Inc.",
    "id": 63,
    "createdAt": "2016-01-19T09:25:27.006661Z",
    "anonymousRecruitment": True
}


def test_check_service_essentials_passes_good_drafts():
    assert check_service_essentials(COMPLETE_OUTCOMES_DRAFT) == 'Pass'
    assert check_service_essentials(COMPLETE_SPECIALISTS_DRAFT) == 'Pass'
    assert check_service_essentials(COMPLETE_STUDIOS_DRAFT) == 'Pass'
    assert check_service_essentials(COMPLETE_RESEARCH_PARTICIPANTS_DRAFT) == 'Pass'


def test_check_service_essentials_fails_bad_participants_drafts():
    bad_participants = COMPLETE_RESEARCH_PARTICIPANTS_DRAFT.copy()
    bad_participants['anonymousRecruitment'] = False
    assert check_service_essentials(bad_participants) == 'Fail'


def test_check_service_essentials_fails_bad_outcomes_drafts():
    bad_outcome = COMPLETE_OUTCOMES_DRAFT.copy()
    bad_outcome['helpGovernmentImproveServices'] = False
    assert check_service_essentials(bad_outcome) == 'Fail'


def test_check_service_essentials_fails_bad_specialists_drafts():
    bad_specialist = COMPLETE_SPECIALISTS_DRAFT.copy()
    bad_specialist['openStandardsPrinciples'] = False
    assert check_service_essentials(bad_specialist) == 'Fail'


def test_check_declaration_fails_incomplete_declaration():
    declaration_content = mock.Mock()
    declaration = {"status": "started"}
    assert check_declaration_answers(declaration_content, declaration) == 'Fail'


def test_check_declaration_answers_passes_good_declaration():
    declaration_content = mock.Mock()
    question_numbers = mock.PropertyMock(side_effect=[1, 17, 21, -1])
    type(declaration_content.get_question.return_value).number = question_numbers
    # Question 1 should be True; 17 and 21 False
    declaration = OrderedDict([("key1", True), ("key2", False), ("key3", False), ("status", "complete")])
    assert check_declaration_answers(declaration_content, declaration) == 'Pass'


def test_check_declaration_answers_fails_bad_declaration_true_is_false():
    declaration_content = mock.Mock()
    question_numbers = mock.PropertyMock(side_effect=[1, 17, 21, -1])
    type(declaration_content.get_question.return_value).number = question_numbers
    # Question 1 should be True; 17 and 21 False
    # Question 1 is incorrectly False so should Fail
    declaration = OrderedDict([("key1", False), ("key2", False), ("key3", False), ("status", "complete")])
    assert check_declaration_answers(declaration_content, declaration) == 'Fail'


def test_check_declaration_answers_fails_bad_declaration_false_is_true():
    declaration_content = mock.Mock()
    question_numbers = mock.PropertyMock(side_effect=[2, 18, 22, -1])
    type(declaration_content.get_question.return_value).number = question_numbers
    # Question 2 should be True; 18 and 22 False
    # Question 18 is incorrectly True so should Fail
    declaration = OrderedDict([("key1", True), ("key2", True), ("key3", False), ("status", "complete")])
    assert check_declaration_answers(declaration_content, declaration) == 'Fail'


def test_check_declaration_answers_returns_discretionary_for_false_is_true():
    declaration_content = mock.Mock()
    question_numbers = mock.PropertyMock(side_effect=[2, 18, 22, -1])
    type(declaration_content.get_question.return_value).number = question_numbers
    # Question 2 should be True; 18 and 22 False but 22 is a discretionary Fail
    # Question 22 is incorrectly True so should Fail
    declaration = OrderedDict([("key1", True), ("key2", False), ("key3", True), ("status", "complete")])
    assert check_declaration_answers(declaration_content, declaration) == 'Discretionary'


def test_check_declaration_answers_passes_good_q14():
    declaration_content = mock.Mock()
    question_numbers = mock.PropertyMock(side_effect=[14, -1])
    type(declaration_content.get_question.return_value).number = question_numbers
    # Question 14 is the one with two long possible correct answers
    declaration = OrderedDict([("key1", "Not applicable - your organisation does not need employer’s liability "
                                        "insurance because your organisation employs only the owner or close family "
                                        "members."), ("status", "complete")])
    assert check_declaration_answers(declaration_content, declaration) == 'Pass'


def test_check_declaration_answers_fails_for_bad_q14():
    declaration_content = mock.Mock()
    question_numbers = mock.PropertyMock(side_effect=[14, -1])
    type(declaration_content.get_question.return_value).number = question_numbers
    # Question 14 is the one with two long possible correct answers
    declaration = OrderedDict([("key1", "No - this is a really long explanation"), ("status", "complete")])
    assert check_declaration_answers(declaration_content, declaration) == 'Fail'


def test_process_submitted_drafts_for_good_services(mock_data_client):
    mock_data_client.find_draft_services.return_value = {
        "services": [COMPLETE_OUTCOMES_DRAFT, COMPLETE_RESEARCH_PARTICIPANTS_DRAFT]
    }
    assert process_submitted_drafts(mock_data_client, 12345, 'user') is True
    mock_data_client.update_draft_service_status.assert_not_called()


def test_process_submitted_drafts_with_bad_service(mock_data_client):
    bad_service = COMPLETE_RESEARCH_PARTICIPANTS_DRAFT.copy()
    bad_service['anonymousRecruitment'] = False
    bad_service['id'] = 42
    mock_data_client.find_draft_services.return_value = {
        "services": [bad_service]
    }
    assert process_submitted_drafts(mock_data_client, 12345, 'user') is False
    mock_data_client.update_draft_service_status.assert_called_with(42, 'failed', 'user')


def test_process_submitted_drafts_with_bad_and_good_service(mock_data_client):
    bad_service = COMPLETE_RESEARCH_PARTICIPANTS_DRAFT.copy()
    bad_service['anonymousRecruitment'] = False
    bad_service['id'] = 24
    mock_data_client.find_draft_services.return_value = {
        "services": [bad_service, COMPLETE_STUDIOS_DRAFT]
    }
    assert process_submitted_drafts(mock_data_client, 12345, 'user') is True
    mock_data_client.update_draft_service_status.assert_called_with(24, 'failed', 'user')


def test_process_dos_results_for_successful(mock_data_client):
    declaration_content = mock.Mock()
    question_numbers = mock.PropertyMock(side_effect=[2, 18, 22, -1])
    type(declaration_content.get_question.return_value).number = question_numbers

    content_loader = mock.Mock()
    content_loader.get_manifest.return_value = declaration_content

    declaration = OrderedDict([("key1", True), ("key2", False), ("key3", False), ("status", "complete")])
    mock_data_client.get_interested_suppliers.return_value = {"interestedSuppliers": [123456]}
    mock_data_client.get_supplier_declaration.return_value = {"declaration": declaration}
    mock_data_client.find_draft_services.return_value = {
        "services": [COMPLETE_OUTCOMES_DRAFT, COMPLETE_RESEARCH_PARTICIPANTS_DRAFT]
    }
    process_dos_results(mock_data_client, content_loader, 'user')
    mock_data_client.set_framework_result.assert_called_with(123456, 'digital-outcomes-and-specialists', True, 'user')


def test_process_dos_results_for_incomplete_declaration(mock_data_client):
    declaration_content = mock.Mock()
    question_numbers = mock.PropertyMock(side_effect=[2, 18, 22, -1])
    type(declaration_content.get_question.return_value).number = question_numbers

    content_loader = mock.Mock()
    content_loader.get_manifest.return_value = declaration_content
    # Declaration not complete so application should fail
    declaration = OrderedDict([("key1", True), ("key2", False), ("key3", False), ("status", "started")])
    mock_data_client.get_interested_suppliers.return_value = {"interestedSuppliers": [123456]}
    mock_data_client.get_supplier_declaration.return_value = {"declaration": declaration}
    mock_data_client.find_draft_services.return_value = {
        "services": [COMPLETE_OUTCOMES_DRAFT, COMPLETE_RESEARCH_PARTICIPANTS_DRAFT]
    }
    process_dos_results(mock_data_client, content_loader, 'user')
    mock_data_client.set_framework_result.assert_called_with(123456, 'digital-outcomes-and-specialists', False, 'user')


def test_process_dos_results_for_bad_service_essentials(mock_data_client):
    declaration_content = mock.Mock()
    question_numbers = mock.PropertyMock(side_effect=[2, 18, 22, -1])
    type(declaration_content.get_question.return_value).number = question_numbers

    content_loader = mock.Mock()
    content_loader.get_manifest.return_value = declaration_content
    # Service fails on essential so application should be a fail
    bad_service = COMPLETE_RESEARCH_PARTICIPANTS_DRAFT.copy()
    bad_service['anonymousRecruitment'] = False
    declaration = OrderedDict([("key1", True), ("key2", False), ("key3", False), ("status", "complete")])
    mock_data_client.get_interested_suppliers.return_value = {"interestedSuppliers": [123456]}
    mock_data_client.get_supplier_declaration.return_value = {"declaration": declaration}
    mock_data_client.find_draft_services.return_value = {
        "services": [bad_service]
    }
    process_dos_results(mock_data_client, content_loader, 'user')
    mock_data_client.set_framework_result.assert_called_with(123456, 'digital-outcomes-and-specialists', False, 'user')


def test_process_dos_results_for_one_good_one_bad_service(mock_data_client):
    declaration_content = mock.Mock()
    question_numbers = mock.PropertyMock(side_effect=[2, 18, 22, -1])
    type(declaration_content.get_question.return_value).number = question_numbers

    content_loader = mock.Mock()
    content_loader.get_manifest.return_value = declaration_content
    # Service fails on essential but second lot service is OK so application should Pass overall
    bad_service = COMPLETE_RESEARCH_PARTICIPANTS_DRAFT.copy()
    bad_service['anonymousRecruitment'] = False
    declaration = OrderedDict([("key1", True), ("key2", False), ("key3", False), ("status", "complete")])
    mock_data_client.get_interested_suppliers.return_value = {"interestedSuppliers": [123456]}
    mock_data_client.get_supplier_declaration.return_value = {"declaration": declaration}
    mock_data_client.find_draft_services.return_value = {
        "services": [bad_service, COMPLETE_OUTCOMES_DRAFT]
    }
    process_dos_results(mock_data_client, content_loader, 'user')
    mock_data_client.set_framework_result.assert_called_with(123456, 'digital-outcomes-and-specialists', True, 'user')


def test_process_dos_results_for_one_good_one_bad_service(mock_data_client):
    declaration_content = mock.Mock()
    question_numbers = mock.PropertyMock(side_effect=[2, 18, 22, -1])
    type(declaration_content.get_question.return_value).number = question_numbers

    content_loader = mock.Mock()
    content_loader.get_manifest.return_value = declaration_content
    # Service fails on essential but second lot service is OK so application should Pass overall
    bad_service = COMPLETE_RESEARCH_PARTICIPANTS_DRAFT.copy()
    bad_service['anonymousRecruitment'] = False
    declaration = OrderedDict([("key1", True), ("key2", False), ("key3", False), ("status", "complete")])
    mock_data_client.get_interested_suppliers.return_value = {"interestedSuppliers": [123456]}
    mock_data_client.get_supplier_declaration.return_value = {"declaration": declaration}
    mock_data_client.find_draft_services.return_value = {
        "services": [bad_service, COMPLETE_OUTCOMES_DRAFT]
    }
    process_dos_results(mock_data_client, content_loader, 'user')
    mock_data_client.set_framework_result.assert_called_with(123456, 'digital-outcomes-and-specialists', True, 'user')


def test_process_dos_results_for_successful(mock_data_client):
    declaration_content = mock.Mock()
    question_numbers = mock.PropertyMock(side_effect=[2, 18, 22, -1])
    type(declaration_content.get_question.return_value).number = question_numbers

    content_loader = mock.Mock()
    content_loader.get_manifest.return_value = declaration_content
    # Question 22 = True is a discretionary fail, so result should be discretionary
    declaration = OrderedDict([("key1", True), ("key2", False), ("key3", True), ("status", "complete")])
    mock_data_client.get_interested_suppliers.return_value = {"interestedSuppliers": [123456]}
    mock_data_client.get_supplier_declaration.return_value = {"declaration": declaration}
    mock_data_client.find_draft_services.return_value = {
        "services": [COMPLETE_OUTCOMES_DRAFT, COMPLETE_RESEARCH_PARTICIPANTS_DRAFT]
    }
    process_dos_results(mock_data_client, content_loader, 'user')
    # Discretionary result should not update `supplier_frameworks` at all
    mock_data_client.set_framework_result.assert_not_called()
