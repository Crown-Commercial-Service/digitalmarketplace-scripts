#!/usr/bin/env python
import csv
import itertools
import os
import requests
import json
import time

url = "https://api.trello.com/1/search"
headers = {"Accept": "application/json"}
query = {
    "key": os.environ["TRELLO_KEY"],
    "token": os.environ["TRELLO_TOKEN"],
    "query": "has:attachment",
    "card_fields": "name,url,id",
    "modelTypes": "cards",
    "card_attachments": "true",
    "cards_limit": 100,
}

attachments = []
for page in itertools.count(start=0):
    query["cards_page"] = page

    response = requests.request("GET", url, headers=headers, params=query)

    response.raise_for_status()

    cards = json.loads(response.text)["cards"]

    if not cards:
        break

    attachments.extend(
        [
            {
                "card_name": card["name"],
                "card_url": card["url"],
                "card_id": card["id"],
                "attachment_name": attachment["name"],
                "attachment_id": attachment["id"],
                "attachment_url": attachment["url"],
            }
            for card in cards
            for attachment in card["attachments"]
            if attachment["name"].endswith(".csv")
        ]
    )

    time.sleep(1)
    print(page)

print(attachments)
print(len(attachments))

with open("attachments.csv", "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=attachments[0].keys())
    writer.writeheader()
    writer.writerows(attachments)
