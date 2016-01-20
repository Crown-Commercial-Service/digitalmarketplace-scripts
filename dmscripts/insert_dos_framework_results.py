# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from dmapiclient import HTTPError

CORRECT_DECLARATION_RESPONSE_MUST_BE_TRUE = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 38, 39, 40, 41, 42,
                                             43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54]
CORRECT_DECLARATION_RESPONSE_MUST_BE_FALSE = [17, 18, 19, 20]
CORRECT_DECLARATION_RESPONSE_SHOULD_BE_FALSE = [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 35, 36]
MITIGATING_FACTORS = [34, 37]
CORRECT_DECLARATION_RESPONSES = {14: ["Yes – your organisation has, or will have in place, employer’s liability "
                                      "insurance of at least £5 million and you will provide certification prior "
                                      "to framework award.",
                                      "Not applicable - your organisation does not need employer’s liability "
                                      "insurance because your organisation employs only the owner or close family "
                                      "members."]}
SERVICE_ESSENTIALS_MUST_BE_TRUE = ['helpGovernmentImproveServices', 'bespokeSystemInformation', 'dataProtocols',
                                   'openStandardsPrinciples', 'anonymousRecruitment', 'manageIncentives']
FAIL = "Fail"
PASS = "Pass"
DISCRETIONARY = "Discretionary"


def insert_result(client, supplier_id, result, user):
    try:
        client.set_framework_result(supplier_id, 'digital-outcomes-and-specialists', result, user)
        return"  Result set OK: {}".format(supplier_id)
    except HTTPError as e:
        return"  Error inserting result for {} ({}): {}".format(supplier_id, result, str(e))


def get_submitted_drafts(client, supplier_id):
    services = client.find_draft_services(supplier_id, framework='digital-outcomes-and-specialists')
    services = services["services"]
    submitted_services = [service for service in services if service["status"] == "submitted"]
    return submitted_services


def check_service_essentials(draft):
    for essential in SERVICE_ESSENTIALS_MUST_BE_TRUE:
        if essential in draft and draft[essential] is not True:
            return FAIL
    return PASS


def check_declaration_answers(declaration_content, declaration):
    if declaration['status'] != 'complete':
        return FAIL

    result = PASS
    for (field_name) in declaration:
        question_number = declaration_content.get_question(field_name).number \
            if declaration_content.get_question(field_name) else -1
        if (question_number in CORRECT_DECLARATION_RESPONSE_MUST_BE_TRUE
           and declaration[field_name] is not True):
            print(" Question {} must be True but is {}".format(question_number, declaration[field_name]))
            result = FAIL

        if (question_number in CORRECT_DECLARATION_RESPONSE_MUST_BE_FALSE
           and declaration[field_name] is not False):
            print(" Question {} must be False but is {}".format(question_number, declaration[field_name]))
            result = FAIL

        if (question_number in CORRECT_DECLARATION_RESPONSE_SHOULD_BE_FALSE
           and declaration[field_name] is not False):
            print(" Question {} should be False but is {}".format(question_number, declaration[field_name]))
            if result == PASS:
                result = DISCRETIONARY

        if (question_number in CORRECT_DECLARATION_RESPONSES
           and declaration[field_name] not in CORRECT_DECLARATION_RESPONSES[question_number]):
            print(" Question {} has the wrong answer: {}".format(question_number, declaration[field_name]))
            result = FAIL

    return result


def process_submitted_drafts(client, supplier_id, user):
    submitted_drafts = get_submitted_drafts(client, supplier_id)
    supplier_has_submitted_services = False

    for draft in submitted_drafts:
        draft_result = check_service_essentials(draft)
        if draft_result == PASS:
            supplier_has_submitted_services = True
        else:
            # Update the draft to be 'failed'
            print("  Service essentials failed for draft {} in lot '{}'".format(draft['id'], draft['lot']))
            client.update_draft_service(draft['id'], {"status": "failed"}, user)

    return supplier_has_submitted_services


def process_dos_results(client, content_loader, user):
    content_loader.load_manifest('digital-outcomes-and-specialists', 'declaration', 'declaration')
    declaration_content = content_loader.get_manifest('digital-outcomes-and-specialists', 'declaration')

    dos_registered_suppliers = client\
        .get_interested_suppliers('digital-outcomes-and-specialists')\
        .get('interestedSuppliers', None)

    for supplier_id in dos_registered_suppliers:
        print("SUPPLIER: {}".format(supplier_id))
        declaration = client.get_supplier_declaration(supplier_id, 'digital-outcomes-and-specialists')['declaration']

        declaration_result = check_declaration_answers(declaration_content, declaration) if declaration else FAIL
        supplier_has_submitted_services = process_submitted_drafts(client, supplier_id, user)

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
