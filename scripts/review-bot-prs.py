#!/usr/bin/env python
"""
Show a human bot PRs that look ready to be merged. If the human accepts, approve and merge the PRs.

Requires GitHub's CLI tool: https://github.com/cli/cli

Usage:
    scripts/review-bot-prs.py (snyk | dependabot)
"""

import json
import subprocess
from docopt import docopt

ORGANISATION = "Crown-Commercial-Service"

BOTS_CONFIG = {
    'dependabot': {
        'login': 'dependabot',
        'search_fragment': 'label:dependencies'
    },
    'snyk': {
        'search_fragment': 'snyk'
    }
}


def get_digital_marketplace_repos():
    output = subprocess.run(
        [
            "gh",
            "api",
            "--paginate",
            f"/orgs/{ORGANISATION}/teams/digitalmarketplace-admin/repos",  # team with access to all DMP repos
        ],
        stdout=subprocess.PIPE,
        check=True,
    )

    return {repo["name"] for repo in json.loads(output.stdout) if not repo["archived"]}


def open_pull_request_in_browser(pr_url):
    subprocess.run(
        [
            "gh",
            "pr",
            "view",
            "--web",
            pr_url,
        ],
        check=True,
    )


def is_check_successful(check):
    return (
        check["status"] == "COMPLETED"
        and check["conclusion"] == "SUCCESS"  # Github Actions
        or check.get("state") == "SUCCESS"  # Snyk
    )


def eligible_for_semiautomated_merge(pr):
    if pr["state"] != "OPEN":
        print(f'Wrong state: {pr["state"]}')
        return False
    if pr["reviews"]:
        print(f'Wrong reviews: {pr["reviews"]}')
        return False
    if expected_user := BOTS_CONFIG[BOT].get("login"):
        if pr["author"] != {"login": expected_user}:
            print(f'Wrong author: {pr["author"]}')
            return False
    if pr["mergeable"] != "MERGEABLE":
        print(f'Wrong mergeable: {pr["mergeable"]}')
        return False
    if not pr["statusCheckRollup"]:
        print(f'Wrong statusCheckRollup: {pr["statusCheckRollup"]}')
        return False
    unsuccessful_checks = [
        check for check in pr["statusCheckRollup"] if not is_check_successful(check)
    ]
    if unsuccessful_checks:
        print(f"Unsuccessful checks: {unsuccessful_checks}")
        return False
    return True


def check_gh_installed():
    try:
        subprocess.run(["which", "gh"], check=True)
    except subprocess.CalledProcessError as e:
        print("You are missing the `gh` CLI tool. Install it from https://github.com/cli/cli#installation")
        raise e


if __name__ == "__main__":
    arguments = docopt(__doc__)

    check_gh_installed()

    BOT = 'snyk' if arguments['snyk'] else 'dependabot'

    github_repo_string = " ".join(
        f"repo:{ORGANISATION}/{repo}" for repo in get_digital_marketplace_repos()
    )

    output = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "--json",
            "author,number,mergeable,reviews,state,title,url,statusCheckRollup,headRepository",
            "--search",
            f"{BOTS_CONFIG[BOT]['search_fragment']} state:open is:pr {github_repo_string}",
        ],
        stdout=subprocess.PIPE,
        check=True,
    )

    bot_prs = json.loads(output.stdout)
    bot_prs.sort(key=lambda pr: pr["title"])
    repos_merged_to = set()

    for pr in bot_prs:
        repository = pr["headRepository"]["name"]

        print(f"\n# {repository}: {pr['title']}")
        print(pr["url"])

        if not eligible_for_semiautomated_merge(pr):
            print("Skipping")
            continue
        if repository in repos_merged_to:
            print(f"Skipping: already merged a PR to {repository}")
            continue

        print(f"Approve and merge '{pr['title']}'?")
        open_pull_request_in_browser(pr["url"])
        approve = input("Enter 'y' to approve and merge ")

        if approve == "y":
            print("Approving and merging")
            subprocess.run(["gh", "pr", "review", "--approve", pr["url"]], check=True)
            subprocess.run(["gh", "pr", "merge", "--merge", pr["url"]], check=True)
            repos_merged_to.add(repository)
        else:
            print("Skipping")
