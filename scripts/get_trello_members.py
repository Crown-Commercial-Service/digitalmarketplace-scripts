#!/usr/bin/env python
"""
Get all members of all boards owned by all our organisations. You need to be a member of all our organisations to be
able to run this script.
"""
import os
import requests
import json

BASE_URL = "https://api.trello.com/1"
HEADERS = {"Accept": "application/json"}
QUERY = {
    "key": os.environ["TRELLO_KEY"],
    "token": os.environ["TRELLO_TOKEN"],
}


def get_organisations():
    """
    All the DMp Trello organisations.
    """
    return {
        "DMP 2": "5e70a808f51fba20f624d9e2",  # pragma: allowlist secret
        "DMP 3": "5eb0095a4b182882dbb46652",  # pragma: allowlist secret
        "DMP 4": "5f11bf47fb7c2f529c42193a",  # pragma: allowlist secret
        "Digital Marketplace - up to May 2019": "56ab94d6239d393aafcc0dd7",  # pragma: allowlist secret
        "Digital Marketplace Missions": "5cd16b6993f4f0616b48c101",  # pragma: allowlist secret
        "Digital Marketplace UR": "5cc18c22ae0b160c5229e07e",  # pragma: allowlist secret
        "DMP EMPATHY LAB": "5e99bd017496273606e74187",  # pragma: allowlist secret
    }.values()


def get_organisation_boards(organisation_id):
    response = requests.request(
        "GET",
        f"{BASE_URL}/organizations/{organisation_id}/boards",
        headers=HEADERS,
        params=QUERY,
    )
    response.raise_for_status()
    return [(board["id"], board["name"]) for board in json.loads(response.text)]


boards = [
    board
    for organisation_id in get_organisations()
    for board in get_organisation_boards(organisation_id)
]

print(f"Board count: {len(boards)}")

members = {}
for (board_id, board_name) in boards:
    response = requests.request(
        "GET",
        f"{BASE_URL}/boards/{board_id}/memberships",
        headers=HEADERS,
        params={"member": "true", **QUERY},
    )
    response.raise_for_status()

    for person in json.loads(response.text):
        members.setdefault(person["member"]["username"], []).append(board_name)

print(members.keys())
print(members)
