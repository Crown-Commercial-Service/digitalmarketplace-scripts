#!/usr/bin/env python
"""
Shows all the repos controlled by the Digital Marketplace team, and whether they should be transferred to CCS
"""
import json
import subprocess

DIGITAL_MARKETPLACE_TEAMS = {"digitalmarketplace", "digitalmarketplace-admin", "digitalmarketplace-readonly"}


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


if __name__ == "__main__":
    admin_repos = get_repos_for_team("digitalmarketplace-admin")

    print(admin_repos)
    print(len(admin_repos))

    # non_admin_repos = get_repos_for_team("digitalmarketplace") - admin_repos
    #
    # print(non_admin_repos)
    # print(len(non_admin_repos))

    # read_only_repos = get_repos_for_team("digitalmarketplace-readonly") - admin_repos - non_admin_repos
    # if read_only_repos:
    #     raise Exception("There should be no repos accessible only to the read-only team")

    for repo in admin_repos:
        output = subprocess.run(
            [
                "gh",
                "api",
                "--paginate",
                f"/repos/alphagov/{repo}/teams",
            ],
            stdout=subprocess.PIPE,
            check=True,
        )
        external_teams = {team['name'] for team in json.loads(output.stdout)} - DIGITAL_MARKETPLACE_TEAMS

        print(f"{repo}: {external_teams}")
