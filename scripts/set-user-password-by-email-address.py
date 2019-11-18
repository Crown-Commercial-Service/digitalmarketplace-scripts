#!/usr/bin/env python3
"""
    This script isn't really intended to be run on its own, instead being called from rotate-api-tokens.sh.
    If you are going to run it on its own, it expects the following environment variables to be set:
     - STAGE: preview, staging or production
     - ACCOUNT_EMAIL: the email address of the DMP account whose password is to be changed
     - ACCOUNT_PASSWORD: the new password for the DMP account

    DM_CREDENTIALS_REPO may also be needed to retrieve the required API tokens
"""

import sys

sys.path.insert(0, '.')

from os import environ
from sys import exit

from dmapiclient import DataAPIClient
from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage

if __name__ == "__main__":
    data_api_client = DataAPIClient(
        get_api_endpoint_from_stage(environ["STAGE"].lower()),
        get_auth_token('api', environ["STAGE"].lower()),
    )

    email_address = environ["ACCOUNT_EMAIL"]
    user = data_api_client.get_user(email_address=email_address)
    if not user:
        print(f"User {email_address!r} not found")
        exit(2)

    if not data_api_client.update_user_password(
        user["users"]["id"],
        environ["ACCOUNT_PASSWORD"],
        "set-dm-password-by-email.py",
    ):
        print(f"Failed to set password for {email_address!r}")
        exit(3)
