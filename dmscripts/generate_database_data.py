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
        "email_address": generate_email_address(),
        "password": DEFAULT_PASSWORD,
        "role": role,
    }

    data.create_user(user=user)
    return user
