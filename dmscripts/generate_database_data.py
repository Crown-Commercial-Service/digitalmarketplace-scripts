import random
import string
from dmapiclient import DataAPIClient

from typing import Optional

USER_ROLES = [
    'admin',
    'admin-ccs-category',
    'admin-ccs-sourcing',
    'admin-manager',
    'admin-framework-manager',
    'admin-ccs-data-controller',
    'buyer',
    'supplier',
]

G_CLOUD_FRAMEWORK = {
    'allowDeclarationReuse': True,
    'applicationsCloseAtUTC': '2021-07-13T13:36:08.114010Z',
    'clarificationQuestionsOpen': False,
    'clarificationsCloseAtUTC': '2021-07-12T12:58:37.583954Z',
    'clarificationsPublishAtUTC': '2020-07-13T16:00:00.000000Z',
    'countersignerName': 'A G-Cloud Countersigner',
    'family': 'g-cloud',
    'framework': 'g-cloud',
    'frameworkAgreementDetails': {
        'contractNoticeNumber': '2020/S 045-107620',
        'countersignerName': 'A G-Cloud Countersigner',
        'countersignerRole': 'Director - Technology',
        'frameworkAgreementVersion': 'RM1557.12',
        'frameworkExtensionLength': 'Up to 12 months, by CCS giving written notice to Suppliers',
        'frameworkRefDate': '21-09-2020',
        'frameworkURL': 'https://www.gov.uk/government/publications/g-cloud-12-framework-agreement',
        'lotDescriptions': {
            'cloud-hosting': 'Lot 1: Cloud hosting',
            'cloud-software': 'Lot 2: Cloud software',
            'cloud-support': 'Lot 3: Cloud support'
        },
        'lotOrder': ['cloud-hosting', 'cloud-software', 'cloud-support'],
        'variations': {}
    },
    'frameworkAgreementVersion': 'RM1557.12',
    'frameworkExpiresAtUTC': '2021-09-27T12:00:00.000000Z',
    'frameworkLiveAtUTC': '2021-08-04T11:59:37.430818Z',
    'hasDirectAward': True,
    'hasFurtherCompetition': False,
    'intentionToAwardAtUTC': '2020-09-01T12:00:00.000000Z',
    'isESignatureSupported': True,
    'lots': [
        {
            'allowsBrief': False,
            'name': 'Cloud hosting',
            'oneServiceLimit': False,
            'slug': 'cloud-hosting',
            'unitPlural': 'services',
            'unitSingular': 'service'
        },
        {
            'allowsBrief': False,
            'name': 'Cloud software',
            'oneServiceLimit': False,
            'slug': 'cloud-software',
            'unitPlural': 'services',
            'unitSingular': 'service'
        },
        {
            'allowsBrief': False,
            'name': 'Cloud support',
            'oneServiceLimit': False,
            'slug': 'cloud-support',
            'unitPlural': 'services',
            'unitSingular': 'service'
        }
    ],
    'status': 'live',
    'name': 'G-Cloud 12',
    'slug': 'g-cloud-12',
    'variations': {}
}

DEFAULT_PASSWORD = "Password1234"


def generate_email_address(username: Optional[int] = None) -> str:
    """Generate an email of the form 123456@user.marketplace.team"""
    if username is not None:
        return f"{username}@user.marketplace.team"
    else:
        return f"{random.randrange(1, 10 ** 6):06}@user.marketplace.team"


def random_string_of_length(n: int = 10) -> str:
    return ''.join(random.choice(string.ascii_letters) for _ in range(n))


def generate_user(data: DataAPIClient, role: str) -> dict:
    """Generate a new user with randomised data and store it in the API"""

    if role not in USER_ROLES:
        raise ValueError(f"role: {role} not a valid user role")
    user = {
        "name": random_string_of_length(10),
        "emailAddress": generate_email_address(),
        "password": DEFAULT_PASSWORD,
        "role": role,
    }

    data.create_user(user=user)
    return user


def create_buyer_email_domain_if_not_present(data: DataAPIClient, email_domain: str):
    if email_domain not in {d["domainName"] for d in data.get_buyer_email_domains_iter()}:
        data.create_buyer_email_domain(email_domain)


def set_all_frameworks_to_expired(data: DataAPIClient) -> None:
    for framework in data.find_frameworks().get("frameworks", []):
        if framework["status"] != "expired":
            data.update_framework(framework_slug=framework["slug"], data={"status": "expired"})


def make_gcloud_12_live(data: DataAPIClient) -> None:
    data.update_framework(
        framework_slug=G_CLOUD_FRAMEWORK["slug"],
        data={
            "status": G_CLOUD_FRAMEWORK["status"]
        }
    )


def open_gcloud_12(data: DataAPIClient) -> None:
    existing_frameworks = [f["slug"] for f in data.find_frameworks().get("frameworks", [])]
    if G_CLOUD_FRAMEWORK["slug"] not in existing_frameworks:
        data.create_framework(
            slug=G_CLOUD_FRAMEWORK["slug"],
            name=G_CLOUD_FRAMEWORK["name"],
            framework_family_slug=G_CLOUD_FRAMEWORK["family"],
            lots=[lot["slug"] for lot in G_CLOUD_FRAMEWORK["lots"]],
            has_further_competition=False,
            has_direct_award=True,
            status="open"
        )

        data.update_framework(
            framework_slug=G_CLOUD_FRAMEWORK["slug"],
            data={
                "allowDeclarationReuse": G_CLOUD_FRAMEWORK["allowDeclarationReuse"],
                "applicationsCloseAtUTC": G_CLOUD_FRAMEWORK["applicationsCloseAtUTC"],
                "intentionToAwardAtUTC": G_CLOUD_FRAMEWORK["intentionToAwardAtUTC"],
                "clarificationsCloseAtUTC": G_CLOUD_FRAMEWORK["clarificationsCloseAtUTC"],
                "clarificationsPublishAtUTC": G_CLOUD_FRAMEWORK["clarificationsPublishAtUTC"],
                "frameworkLiveAtUTC": G_CLOUD_FRAMEWORK["frameworkLiveAtUTC"],
                "frameworkExpiresAtUTC": G_CLOUD_FRAMEWORK["frameworkExpiresAtUTC"]
            }
        )

    # Regardless of whether the framework was already in the db, we want to make sure a couple of attributes
    # are properly set
    # Unfortunately I need to update `status` and `clarificationQuestionsOpen` in two different operations, otherwise
    # I get this error message:
    # dmapiclient.errors.HTTPError: Clarification questions are only permitted while the framework is open (status: 400)
    data.update_framework(
        framework_slug=G_CLOUD_FRAMEWORK["slug"],
        data={
            "status": "open"
        }
    )
    data.update_framework(
        framework_slug=G_CLOUD_FRAMEWORK["slug"],
        data={
            "clarificationQuestionsOpen": True
        }
    )
