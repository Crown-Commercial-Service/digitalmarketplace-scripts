#!/usr/bin/env python
"""
Process the list of Trello attachments produced by get_trello_attachments.py. Delete all attachments that contain
personal information.
"""
import csv
import os
import requests

headers = {"Accept": "application/json"}
query = {
    "key": os.environ["TRELLO_KEY"],
    "token": os.environ["TRELLO_TOKEN"],
}


def delete_attachment(attachment_url):
    requests.delete(attachment_url, headers=headers, params=query).raise_for_status()


with open("attachments.csv") as csvfile:
    attachments = list(csv.DictReader(csvfile))

for attachment_data in attachments:
    response = requests.get(attachment_data["attachment_url"], headers=headers, params=query)
    response.raise_for_status()

    print(f"CARD: {attachment_data['card_name']}")
    print(f"ATTACHMENT: {attachment_data['attachment_name']}")
    print(f"DATA: {response.text[:1000]}")

    if input("Does this contain personal information? (y/n)") == "y":
        print(f"Deleting {attachment_data['attachment_name']}")
        delete_attachment(attachment_data["attachment_url"])
