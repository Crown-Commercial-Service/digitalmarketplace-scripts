#!/usr/bin/env python

import json
import subprocess
from distutils.spawn import find_executable

# From https://github.com/alphagov/seal/blob/main/config/alphagov.yml
DIGITAL_MARKETPLACE_REPOS = [
    "digitalmarketplace-admin-frontend",
    "digitalmarketplace-agreements",
    "digitalmarketplace-antivirus-api",
    "digitalmarketplace-api",
    "digitalmarketplace-apiclient",
    "digitalmarketplace-aws",
    "digitalmarketplace-bad-words",
    "digitalmarketplace-brief-responses-frontend",
    "digitalmarketplace-briefs-frontend",
    "digitalmarketplace-buyer-frontend",
    "digitalmarketplace-content-loader",
    "digitalmarketplace-credentials",
    "digitalmarketplace-developer-tools",
    "digitalmarketplace-docker-base",
    "digitalmarketplace-frameworks",
    "digitalmarketplace-frontend-toolkit",
    "digitalmarketplace-functional-tests",
    "digitalmarketplace-govuk-frontend",
    "digitalmarketplace-jenkins",
    "digitalmarketplace-logdia",
    "digitalmarketplace-manual",
    "digitalmarketplace-performance-testing",
    "digitalmarketplace-router",
    "digitalmarketplace-runner",
    "digitalmarketplace-scripts",
    "digitalmarketplace-search-api",
    "digitalmarketplace-supplier-frontend",
    "digitalmarketplace-test-utils",
    "digitalmarketplace-user-frontend",
    "digitalmarketplace-utils",
    "digitalmarketplace-visual-regression",
    "govuk-frontend-jinja",
]


def open_url_in_browser(url):
    if find_executable("open"):
        # MacOS
        subprocess.run(["open", url])
    elif find_executable("xdg-open"):
        # Linux
        subprocess.run(["xdg-open", url])
    else:
        raise Exception("Unable to find tool to open the URL with")


def eligible_for_semiautomated_merge(pr):
    if pr["state"] != "OPEN":
        print(f'Wrong state: {pr["state"]}')
        return False
    if pr["reviews"]:
        print(f'Wrong reviews: {pr["reviews"]}')
        return False
    if pr["author"] != {"login": "dependabot"}:
        print(f'Wrong author: {pr["author"]}')
        return False
    if pr["mergeable"] != "MERGEABLE":
        print(f'Wrong mergeable: {pr["mergeable"]}')
        return False
    if not pr["statusCheckRollup"]:
        print(f'Wrong statusCheckRollup: {pr["statusCheckRollup"]}')
        return False
    if any(
        check["status"] != "COMPLETED" or check["conclusion"] != "SUCCESS"
        for check in pr["statusCheckRollup"]
    ):
        print("Wrong check status")
        return False
    return True


if __name__ == "__main__":
    github_repo_string = " ".join(
        f"repo:alphagov/{repo}" for repo in DIGITAL_MARKETPLACE_REPOS
    )

    output = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "--json",
            "author,number,mergeable,reviews,state,title,url,statusCheckRollup,headRepository",
            "--search",
            f"label:dependencies state:open is:pr {github_repo_string}",
        ],
        capture_output=True,
        check=True,
    )

    dependabot_prs = json.loads(output.stdout)
    repos_merged_to = set()

    for pr in dependabot_prs:
        print(f"\n# {pr['title']}")
        print(pr["url"])

        if not eligible_for_semiautomated_merge(pr):
            print("Skipping")
            continue
        repository = pr["headRepository"]["name"]
        if repository in repos_merged_to:
            print(f"Skipping: already merged a PR to {repository}")
            continue

        print(f"Approve and merge '{pr['title']}'?")
        open_url_in_browser(pr["url"])
        approve = input("Enter 'y' to approve and merge ")

        if approve == "y":
            print("Approving and merging")
            subprocess.run(["gh", "pr", "review", "--approve", pr["url"]], check=True)
            subprocess.run(["gh", "pr", "merge", "--merge", pr["url"]], check=True)
            repos_merged_to.add(repository)
        else:
            print("Skipping")
