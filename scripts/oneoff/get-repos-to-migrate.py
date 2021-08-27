#!/usr/bin/env python
"""
Shows all the repos controlled by the Digital Marketplace team, and whether they should be transferred to CCS

Usage:
    get-repos-to-migrate.py [--do-migration]
"""
import json
import subprocess
import tempfile

from docopt import docopt

DIGITAL_MARKETPLACE_TEAMS = {
    "digitalmarketplace",
    "digitalmarketplace-admin",
    "digitalmarketplace-readonly",
}

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
    # We need to do this manually so we can set up the necessary Github pages redirect
    "digitalmarketplace-manual",
}

CCS_ORGANISATION = "Crown-Commercial-Service"
CCS_DIGITALMARKETPLACE_TEAM_ID = 5060051
CCS_DIGITALMARKETPLACE_ADMIN_TEAM_ID = 5060056


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

    return {repo["name"] for repo in json.loads(output.stdout)}


def migrate_repo(
    repo_name, source_org, destination_org, new_team_id, do_migration=False
):
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write(
            json.dumps(
                {
                    "new_owner": destination_org,
                    "team_ids": [new_team_id],
                }
            )
        )
        f.flush()

        commands = [
            "echo",
            "gh",
            "api",
            f"/repos/{source_org}/{repo_name}/transfer",
            "--input",
            f.name,
        ]
        if do_migration:
            commands.pop(0)

        subprocess.run(commands, check=True)


if __name__ == "__main__":
    arguments = docopt(__doc__)

    if arguments.get("--do-migration"):
        print("Confirm migration or quit")
        input()
        print("Confirmed. Performing migrations")

    admin_repos = get_repos_for_team("digitalmarketplace-admin") - REPOS_NOT_TO_MIGRATE

    non_admin_repos = (
        get_repos_for_team("digitalmarketplace") - admin_repos - REPOS_NOT_TO_MIGRATE
    )

    read_only_repos = (
        get_repos_for_team("digitalmarketplace-readonly")
        - admin_repos
        - non_admin_repos
        - REPOS_NOT_TO_MIGRATE
    )
    if read_only_repos:
        raise Exception(
            "There should be no repos accessible only to the read-only team"
        )

    for repo in admin_repos:
        print(f"Migrate {repo}: https://github.com/alphagov/{repo}?")
        input()
        migrate_repo(
            repo,
            "alphagov",
            CCS_ORGANISATION,
            CCS_DIGITALMARKETPLACE_ADMIN_TEAM_ID,
            do_migration=arguments.get("--do-migration"),
        )

    for repo in non_admin_repos:
        print(f"Migrate {repo}: https://github.com/alphagov/{repo}?")
        input()
        migrate_repo(
            repo,
            "alphagov",
            CCS_ORGANISATION,
            CCS_DIGITALMARKETPLACE_TEAM_ID,
            do_migration=arguments.get("--do-migration"),
        )
