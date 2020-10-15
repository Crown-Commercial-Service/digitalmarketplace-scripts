#!/usr/bin/env python
"""
Our test supplier in production is on the DOS 4 framework. However, its service has no declaration, which breaks a
few small things. Remove the supplier from DOS 4.
"""
import sys

sys.path.insert(0, ".")
from dmapiclient import DataAPIClient
from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage

data = DataAPIClient(
    get_api_endpoint_from_stage("production"), get_auth_token("api", "production")
)

DMP_TEST_SUPPLIER = 577184
FRAMEWORK = "digital-outcomes-and-specialists-4"
SHOULD_BE_ON_FRAMEWORK = False

data.set_framework_result(
    DMP_TEST_SUPPLIER,
    FRAMEWORK,
    SHOULD_BE_ON_FRAMEWORK,
    user="benjamin.gill@digital.cabinet-office.gov.uk",
)
