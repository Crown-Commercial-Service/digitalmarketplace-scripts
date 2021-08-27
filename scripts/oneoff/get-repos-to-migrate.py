#!/usr/bin/env python
"""
Shows all the repos controlled by the Digital Marketplace team, and whether they should be transferred to CCS
"""
import json
import subprocess

DIGITAL_MARKETPLACE_TEAMS = {"digitalmarketplace", "digitalmarketplace-admin", "digitalmarketplace-readonly"}

REPOS_NOT_TO_MIGRATE = {
    # Repos shared with other teams where we're not admin, so shouldn't migrate them to CCS.
    "gds-cli",
    "gds-tech-learning-pathway",
    "gds-tech-recruitment",
    "gds-way",
    "paas-roadmap",
    "re-rotas",
    "seal",
    # TODO: work out whether to migrate these or not
    "fourth-wall",  # {'team-payments': 'push', 'digitalmarketplace-admin': 'admin', 'GovWifi': 'push'}
    "gds_metrics_python",  # {'digitalmarketplace': 'admin', 're-autom8': 'push'}
    "aws-auth",  # {'digitalmarketplace': 'admin', 'notify': 'push'}
}


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


def get_team_permissions_for_repo(repo_name):
    output = subprocess.run(
        [
            "gh",
            "api",
            "--paginate",
            f"/repos/alphagov/{repo_name}/teams",
        ],
        stdout=subprocess.PIPE,
        check=True,
    )

    return {team['name']: team['permission'] for team in json.loads(output.stdout)}


if __name__ == "__main__":
    admin_repos = get_repos_for_team("digitalmarketplace-admin") - REPOS_NOT_TO_MIGRATE

    print(admin_repos)
    print(len(admin_repos))

    non_admin_repos = get_repos_for_team("digitalmarketplace") - admin_repos - REPOS_NOT_TO_MIGRATE

    print(non_admin_repos)
    print(len(non_admin_repos))

    read_only_repos = get_repos_for_team("digitalmarketplace-readonly") - admin_repos - non_admin_repos - REPOS_NOT_TO_MIGRATE
    if read_only_repos:
        raise Exception("There should be no repos accessible only to the read-only team")

    for repo in admin_repos:
        team_permissions = get_team_permissions_for_repo(repo)
        if team_permissions.keys() - DIGITAL_MARKETPLACE_TEAMS:
            print(f"{repo}: {team_permissions}")

    print()
    print()

    for repo in non_admin_repos:
        team_permissions = get_team_permissions_for_repo(repo)
        if team_permissions.keys() - DIGITAL_MARKETPLACE_TEAMS:
            print(f"{repo}: {team_permissions}")
