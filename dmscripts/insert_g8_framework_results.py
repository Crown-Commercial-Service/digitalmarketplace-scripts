# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from dmapiclient import HTTPError

CORRECT_DECLARATION_RESPONSE_MUST_BE_TRUE = ["termsOfParticipation",
                                             "termsAndConditions",
                                             "readUnderstoodGuidance",
                                             "understandTool",
                                             "understandHowToAskQuestions",
                                             "servicesHaveOrSupport",
                                             "canProvideCloudServices",
                                             "skillsAndResources",
                                             "accuratelyDescribed",
                                             "proofOfClaims",
                                             "MI",
                                             "equalityAndDiversity",
                                             ]
CORRECT_DECLARATION_RESPONSE_MUST_BE_YES_OR_NA = ["employersInsurance"]
CORRECT_DECLARATION_RESPONSE_MUST_BE_FALSE = ["conspiracyCorruptionBribery",
                                              "fraudAndTheft",
                                              "terrorism",
                                              "organisedCrime",
                                              ]

CORRECT_DECLARATION_RESPONSE_SHOULD_BE_FALSE = ["taxEvasion",
                                                "environmentalSocialLabourLaw",
                                                "bankrupt",
                                                "graveProfessionalMisconduct",
                                                "distortingCompetition",
                                                "conflictOfInterest",
                                                "distortedCompetition",
                                                "significantOrPersistentDeficiencies",
                                                "seriousMisrepresentation",
                                                "witheldSupportingDocuments",
                                                "influencedContractingAuthority",
                                                "confidentialInformation",
                                                "misleadingInformation",
                                                "unspentTaxConvictions",
                                                "GAAR",
                                                ]

MITIGATING_FACTORS = ["mitigatingFactors", "mitigatingFactors2"]

FAIL = "Fail"
PASS = "Pass"
DISCRETIONARY = "Discretionary"


def insert_result(client, supplier_id, result, user):
    try:
        client.set_framework_result(supplier_id, 'g-cloud-8', result, user)
        return"  Result set OK: {}".format(supplier_id)
    except HTTPError as e:
        return"  Error inserting result for {} ({}): {}".format(supplier_id, result, str(e))


def get_submitted_drafts(client, supplier_id):
    services = client.find_draft_services(supplier_id, framework='g-cloud-8')
    services = services["services"]
    submitted_services = [service for service in services if service["status"] == "submitted"]
    return submitted_services


def check_declaration_answers(declaration):
    if declaration['status'] != 'complete':
        return FAIL

    result = PASS
    for (field_name) in declaration:
        if (field_name in CORRECT_DECLARATION_RESPONSE_MUST_BE_TRUE
           and declaration[field_name] is not True):
            print(" Question {} must be True but is {}".format(field_name, declaration[field_name]))
            result = FAIL

        if (field_name in CORRECT_DECLARATION_RESPONSE_MUST_BE_FALSE
           and declaration[field_name] is not False):
            print(" Question {} must be False but is {}".format(field_name, declaration[field_name]))
            result = FAIL

        if (field_name in CORRECT_DECLARATION_RESPONSE_SHOULD_BE_FALSE
           and declaration[field_name] is not False):
            print(" Question {} should be False but is {}".format(field_name, declaration[field_name]))
            if result == PASS:
                result = DISCRETIONARY

        if (field_name in CORRECT_DECLARATION_RESPONSE_MUST_BE_YES_OR_NA
           and declaration[field_name] not in ["Yes", "Not applicable"]):
            print(" Question {} has the wrong answer: {}".format(field_name, declaration[field_name]))
            result = FAIL

    return result


def has_supplier_submitted_services(client, supplier_id):
    submitted_drafts = get_submitted_drafts(client, supplier_id)
    if len(submitted_drafts) > 0:
        return True
    else:
        return False


def process_g8_results(client, user):

    g8_registered_suppliers = client\
        .get_interested_suppliers('g-cloud-8')\
        .get('interestedSuppliers', None)

    for supplier_id in g8_registered_suppliers:
        print("SUPPLIER: {}".format(supplier_id))
        declaration = client.get_supplier_declaration(supplier_id, 'g-cloud-8')['declaration']
        declaration_result = check_declaration_answers(declaration) if declaration else FAIL
        supplier_has_submitted_services = has_supplier_submitted_services(client, supplier_id)
        if declaration_result == PASS and supplier_has_submitted_services:
            print("  PASSED")
            res = insert_result(client, supplier_id, True, user)
            print(res)

        elif declaration_result == DISCRETIONARY and supplier_has_submitted_services:
            print("  DISCRETIONARY")
            # No-op here: leave result as NULL in the database
        else:
            print("  FAILED")
            res = insert_result(client, supplier_id, False, user)
            print(res)
