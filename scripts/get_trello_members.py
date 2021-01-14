#!/usr/bin/env python
"""
Get all members of all boards owned by organisations you are part of.
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
    response = requests.request(
        "GET",
        f"{BASE_URL}/members/me/organizations",
        headers=HEADERS,
        params={"fields ": "name", **QUERY},
    )
    response.raise_for_status()
    return [o["id"] for o in json.loads(response.text)]


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
