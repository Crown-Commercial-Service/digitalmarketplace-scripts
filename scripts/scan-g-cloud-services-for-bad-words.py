#!/usr/bin/env python

"""
This script will check all free-text fields in submitted G-Cloud services for "bad words", as defined in
the file at <bad_words_path> (typically blacklist.txt in https://github.com/alphagov/digitalmarketplace-bad-words),
and generate a CSV report of any bad word found.

Usage:
    scripts/scan-g-cloud-services-for-bad-words.py <stage> <bad_words_path> <framework_slug> <output_dir>
"""

import sys
from collections import Counter

sys.path.insert(0, '.')
import os
import csv
import re
from docopt import docopt
from dmapiclient import DataAPIClient
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging

logger = logging_helpers.configure_logger({"dmapiclient": logging.WARNING})

# These are all the free-text boxes in G-Cloud service submissions. They inlude all the keys from G7 through G10.
KEYS_TO_CHECK = (
    'accessRestrictionManagementAndSupport', 'accreditationsOtherList', 'APIAutomationToolsOther', 'apiType',
    'APIUsage', 'approachToResilience', 'backupControls', 'backupWhatData', 'commandLineUsage',
    'configurationAndChangeManagementProcesses', 'customisationDescription', 'dataExportFormatsOther', 'dataExportHow',
    'dataImportFormatsOther', 'dataProtectionBetweenNetworksOther', 'dataProtectionWithinNetworkOther',
    'deprovisioningTime', 'documentationFormatsOther', 'emailOrTicketingSupportResponseTimes',
    'endOfContractDataExtraction', 'endOfContractProcess', 'freeVersionDescription', 'freeVersionLink',
    'gettingStarted', 'guaranteedAvailability', 'incidentManagementApproach', 'independenceOfResources',
    'informationSecurityPoliciesAndProcesses', 'managementAccessAuthenticationDescription', 'metricsDescription',
    'metricsSoftwareDescription', 'metricsWhatOther', 'mobileDifferences', 'ongoingSupportDescription',
    'outageReporting', 'planningServiceCompatibilityList', 'planningServiceDescription', 'protectionOfDataAtRestOther',
    'protectiveMonitoringApproach', 'provisioningTime', 'publicSectorNetworksOther', 'QAAndTestingDescription',
    'resellingOrganisations', 'securityGovernanceApproach', 'securityGovernanceStandardsOther',
    'securityTestingAccreditationsOther', 'securityTestingWhatOther', 'serviceAddOnDetails', 'serviceBenefits',
    'serviceCategoriesSoftware', 'serviceConstraints', 'serviceConstraintsHostingAndSoftware',
    'serviceConstraintsSupport', 'serviceDescription', 'serviceFeatures', 'serviceInterfaceAccessibilityDescription',
    'serviceInterfaceTesting', 'serviceName', 'serviceSummary', 'setupAndMigrationServiceDescription',
    'setupAndMigrationServiceSpecificList', 'standardsCSASTARExclusions', 'standardsCSASTARWhen',
    'standardsISO28000Exclusions', 'standardsISO28000When', 'standardsISO28000Who', 'standardsISOIEC27001Exclusions',
    'standardsISOIEC27001When', 'standardsISOIEC27001Who', 'standardsPCIExclusions', 'standardsPCIWhen',
    'standardsPCIWho', 'supportAvailability', 'supportLevels', 'supportResponseTime', 'systemRequirements',
    'trainingDescription', 'trainingServiceSpecificList', 'userAuthenticationDescription', 'vendorCertifications',
    'virtualisationSeparation', 'virtualisationTechnologiesUsedOther', 'virtualisationThirdPartyProvider',
    'vulnerabilityManagementApproach', 'webChatSupportAccessibilityDescription', 'webChatSupportAccessibilityTesting',
    'webInterfaceAccessibilityDescription', 'webInterfaceAccessibilityTesting', 'webInterfaceUsage'
)

BAD_WORDS_COUNTER = Counter()


def main(stage, data_api_token, bad_words_path, framework_slug, output_dir):
    api_url = get_api_endpoint_from_stage(stage)
    client = DataAPIClient(api_url, data_api_token)
    bad_words = get_bad_words(bad_words_path)
    suppliers = get_suppliers(client, framework_slug)
    check_services_with_bad_words(output_dir, framework_slug, client, suppliers, bad_words)


def get_suppliers(client, framework_slug):
    suppliers = client.find_framework_suppliers(framework_slug)
    suppliers = suppliers["supplierFrameworks"]
    if framework_slug == "g-cloud-6":
        suppliers_on_framework = suppliers
    else:
        suppliers_on_framework = [supplier for supplier in suppliers if supplier["onFramework"]]
    return suppliers_on_framework


def get_services(client, supplier_id, framework_slug):
    services = client.find_services(supplier_id, framework=framework_slug)
    services = services["services"]
    return services


def get_bad_words(bad_words_path):
    with open(bad_words_path) as file:
        lines = file.readlines()
        return [line.strip() for line in lines if not (line.startswith("#") or line.isspace())]


def check_services_with_bad_words(output_dir, framework_slug, client, suppliers, bad_words):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open('{}/{}-services-with-blacklisted-words.csv'.format(
            output_dir, framework_slug), 'w') as csvfile:
        fieldnames = [
            'Supplier ID',
            'Framework',
            'Service ID',
            'Service Name',
            'Service Description',
            'Blacklisted Word Location',
            'Blacklisted Word Context',
            'Blacklisted Word',
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect='excel')
        writer.writeheader()
        for supplier in suppliers:
            try:
                services = get_services(client, supplier["supplierId"], framework_slug)
            except Exception:
                # Retry once; will fail the script if retry fails.
                services = get_services(client, supplier["supplierId"], framework_slug)
            for service in services:
                for key in KEYS_TO_CHECK:
                    if isinstance(service.get(key), str):
                        for word in bad_words:
                            if get_bad_words_in_value(word, service.get(key)):
                                output_bad_words(
                                    supplier["supplierId"],
                                    framework_slug,
                                    service["id"],
                                    service["serviceName"],
                                    service.get("serviceSummary", service.get("serviceDescription")),
                                    key,
                                    service.get(key),
                                    word,
                                    writer)
                                BAD_WORDS_COUNTER.update({word: 1})
                    elif isinstance(service.get(key), list):
                        for contents in service.get(key):
                            for word in bad_words:
                                if get_bad_words_in_value(word, contents):
                                    output_bad_words(
                                        supplier["supplierId"],
                                        framework_slug,
                                        service["id"],
                                        service["serviceName"],
                                        service.get("serviceSummary", service.get("serviceDescription")),
                                        key,
                                        contents,
                                        word,
                                        writer)
                                    BAD_WORDS_COUNTER.update({word: 1})


def get_bad_words_in_value(bad_word, value):
    if re.search(r"\b{}\b".format(bad_word), value, re.IGNORECASE):
        return True


def output_bad_words(
        supplier_id, framework, service_id, service_name,
        service_description, blacklisted_word_location,
        blacklisted_word_context, blacklisted_word, writer):
    row = {
        'Supplier ID': supplier_id,
        'Framework': framework,
        'Service ID': service_id,
        'Service Name': service_name,
        'Service Description': service_description,
        'Blacklisted Word Location': blacklisted_word_location,
        'Blacklisted Word Context': blacklisted_word_context,
        'Blacklisted Word': blacklisted_word,
    }
    logger.info("{} - {}".format(blacklisted_word, service_id))
    writer.writerow(row)


if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(
        arguments['<stage>'], get_auth_token('api', arguments['<stage>']), arguments['<bad_words_path>'],
        arguments['<framework_slug>'], arguments['<output_dir>'])
    logger.info("BAD WORD COUNTS: {}".format(BAD_WORDS_COUNTER))
