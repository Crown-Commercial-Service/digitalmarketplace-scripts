# coding=utf-8

import random


def eligible_g9_declaration_base():
    return {
        "unfairCompetition": True, "offerServicesYourselves": True,
        "fullAccountability": True, "termsOfParticipation": True, "termsAndConditions": True,
        "canProvideFromDayOne": True, "10WorkingDays": True, "MI": True, "conspiracy": False,
        "corruptionBribery": False, "fraudAndTheft": False, "terrorism": False, "organisedCrime": False,
        "taxEvasion": False, "environmentalSocialLabourLaw": False, "bankrupt": False,
        "graveProfessionalMisconduct": False, "distortingCompetition": False, "conflictOfInterest": False,
        "distortedCompetition": False, "significantOrPersistentDeficiencies": False, "seriousMisrepresentation": False,
        "witheldSupportingDocuments": False, "influencedContractingAuthority": False, "confidentialInformation": False,
        "misleadingInformation": False, "mitigatingFactors": "Money is no object", "unspentTaxConvictions": False,
        "GAAR": False, "mitigatingFactors2": "Project favourably entertained by auditors",
        "environmentallyFriendly": True, "equalityAndDiversity": True,
        "employersInsurance": u"Not applicable - your organisation does not need employer’s liability insurance because"
                              u" your organisation employs only the owner or close family members. ",
        "publishContracts": True, "readUnderstoodGuidance": True, "understandTool": True,
        "understandHowToAskQuestions": True, "accurateInformation": True, "informationChanges": True,
        "accuratelyDescribed": True, "proofOfClaims": True,
        "nameOfOrganisation": "Mr Malachi Mulligan. Fertiliser and Incubator.",
        "tradingNames": "Omphalos dutiful yeoman services", "registeredAddressBuilding": "Omphalos",
        "registeredAddressTown": "Lambay Island", "registeredAddressPostcode": "N/A", "firstRegistered": "5/6/1904",
        "currentRegisteredCountry": u"Éire", "companyRegistrationNumber": "00000014", "dunsNumber": "987654321",
        "registeredVATNumber": "123456789", "establishedInTheUK": False, "appropriateTradeRegisters": True,
        "appropriateTradeRegistersNumber": "242#353", "licenceOrMemberRequired": "none of the above",
        "licenceOrMemberRequiredDetails": "",
        "subcontracting": ["yourself without the use of third parties (subcontractors)", ], "organisationSize": "small",
        "tradingStatus": "other (please specify)", "tradingStatusOther": "Proposed", "primaryContact": "B. Mulligan",
        "primaryContactEmail": "buck@example.com", "contactNameContractNotice": "Malachi Mulligan",
        "contactEmailContractNotice": "malachi@example.com", "servicesHaveOrSupport": True,
        "servicesDoNotInclude": True, "payForWhatUse": True, "helpBuyersComplyTechnologyCodesOfPractice": True,
        "status": "complete"
    }


# Just some word lists to generate random cloudy service names.
SERVICE_QUESTIONABLE_ADJECTIVES = ['shiny', 'fractal', 'golden', 'sublime', 'self-replicating', 'superlative',
                                   'impenetrable', 'fully-managed', 'wonderful', 'cost-effective', 'secure',
                                   'certified', 'accredited', 'cybernetic', 'quantum', 'cutting-edge', 'AI-powered']
SERVICE_ADJECTIVES = ['new', 'modern', 'high', 'advanced', 'medical', 'current', 'appropriate', 'military', 'digital',
                      'nuclear', 'available', 'latest', 'western', 'foreign', 'industrial', 'agricultural',
                      'educational', 'sophisticated', 'electronic', 'improved', 'wireless', 'innovative', 'assistive',
                      'instructional', 'superior', 'artisanal', 'conventional', 'complex', 'optical', 'intensive',
                      'scientific', 'proprietary', 'underlying', 'mechanical', 'newer', 'contemporary', 'integrated',
                      'indigenous', 'laser', 'efficient', 'genetic', 'mobile', 'intermediate', 'alternative',
                      'solar', 'interactive', 'clean', 'mature', 'primitive', 'modem', 'oriented', 'electrical',
                      'developed', 'promising', 'ceramic', 'multimedia', 'containerised']
SERVICE_TYPES = ['text', 'online', 'e-service', 'insight', 'intelligence', 'mainframe', 'marketing', 'quality',
                 'digital', 'dynamic', 'engagement', 'discovery', 'solutions', 'strategy', 'transformation',
                 'evaluation', 'advisory', 'physical', 'threat', 'fraud', 'improvement', 'detection', 'waterfall',
                 'managed', 'delivery']
SERVICE_NOUNS = ['security', 'workspace', 'portal', 'platform', 'solution', 'module', 'form', 'strategy', 'development',
                 'search', 'engine', 'manager', 'engineer', 'developer', 'stack', 'environment', 'cloud', 'store',
                 'database', 'healthcheck', 'optimiser', 'doctor', 'intelligence', 'support', 'analyst', 'tools',
                 'course', 'omni-channel hub', 'assistant', 'gateway', 'processor', 'container', 'neural net', 'node',
                 'dashboard', 'visualiser', 'system', 'network', 'suite']


def gen_gcloud_name():
    service_name = '{} {} {}'.format(random.choice(SERVICE_ADJECTIVES),
                                     random.choice(SERVICE_TYPES),
                                     random.choice(SERVICE_NOUNS))
    if random.randint(1, 5) == 1:
        service_name = '{} {}'.format(random.choice(SERVICE_QUESTIONABLE_ADJECTIVES),
                                      service_name)

    return service_name.title()
