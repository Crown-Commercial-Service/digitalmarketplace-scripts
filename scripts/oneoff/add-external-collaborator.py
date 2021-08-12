#!/usr/bin/env python
"""
Add an external collaborator to all our repos. Must be run by a GitHub admin.

Usage:
    add-external-collaborator.py <username>

See https://docs.github.com/en/rest/reference/orgs#outside-collaborators for removal instructions.

Requires GitHub's CLI tool: https://github.com/cli/cli
"""
import subprocess

import requests
import yaml
from docopt import docopt


def get_digital_marketplace_repos():
    response = requests.get(
        "https://raw.githubusercontent.com/alphagov/seal/main/config/alphagov.yml"
    )
    response.raise_for_status()

    return yaml.safe_load(response.text)["digitalmarketplace"]["include_repos"]


if __name__ == "__main__":
    arguments = docopt(__doc__)
    username = arguments["<username>"]

    for repository in get_digital_marketplace_repos():
        print(f"Adding {username} to {repository}")
        # Follows https://docs.github.com/en/rest/reference/repos#add-a-repository-collaborator.
        subprocess.run(
            [
                "gh",
                "api",
                "--silent",
                "--method",
                "PUT",
                f"repos/alphagov/digitalmarketplace-credentials/collaborators/{username}",
            ],
            check=True,
        )
