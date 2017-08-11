import os
import subprocess
import yaml


def get_auth_token(api, stage):
    DM_CREDENTIALS_REPO = os.environ.get('DM_CREDENTIALS_REPO')
    token_prefix = 'J' if subprocess.check_output(["whoami"]) == 'jenkins' else 'D'
    creds = subprocess.check_output([
        "{}/sops-wrapper".format(DM_CREDENTIALS_REPO),
        "-d",
        "{}/vars/{}.yaml".format(DM_CREDENTIALS_REPO, stage)
    ])
    auth_tokens = yaml.load(creds)[api]['auth_tokens']
    auth_token = [token for token in auth_tokens if token.startswith(token_prefix)]

    return auth_token[0]
