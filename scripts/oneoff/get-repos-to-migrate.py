#!/usr/bin/env python
"""
Shows all the repos controlled by the Digital Marketplace team, and whether they should be transferred to CCS
"""
import json
import subprocess

DIGITAL_MARKETPLACE_TEAMS = ["digitalmarketplace", "digitalmarketplace-admin", "digitalmarketplace-readonly"]


def get_repos_for_team(team_name):
    output = subprocess.run(
        [
            "gh",
            "api",
            "--paginate",
            f"/orgs/alphagov/teams/{team_name}/repos",
        ],
        stdout=subprocess.PIPE,
        check=True,
    )

    return {repo['name'] for repo in json.loads(output.stdout)}


def get_all_repos():
    return set().union(*[get_repos_for_team(team) for team in DIGITAL_MARKETPLACE_TEAMS])


if __name__ == "__main__":
    repos = get_all_repos()

    print(repos)
    print(len(repos))
