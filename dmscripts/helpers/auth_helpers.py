import os
import subprocess
import yaml

DEV_ALIASES = ('dev', 'development', 'local')


def get_auth_token(api, stage):
    if stage.lower() in DEV_ALIASES:
        return 'myToken'

    env_var_api_name = 'data-api' if api == 'api' else api
    env_var_api_name = env_var_api_name.replace('-', '_')
    env_var = "DM_{}_TOKEN_{}".format(env_var_api_name.upper(), stage.upper())
    auth_token = os.environ.get(env_var)

    if not auth_token:
        DM_CREDENTIALS_REPO = os.environ.get('DM_CREDENTIALS_REPO', '../digitalmarketplace-credentials')
        token_prefix = 'J' if subprocess.check_output(["whoami"]) == 'jenkins' else 'D'
        creds = subprocess.check_output([
            "{}/sops-wrapper".format(DM_CREDENTIALS_REPO),
            "-d",
            "{}/vars/{}.yaml".format(DM_CREDENTIALS_REPO, stage)
        ])
        auth_tokens = yaml.safe_load(creds)[api]['auth_tokens']
        auth_token = next(token for token in auth_tokens if token.startswith(token_prefix))

    return auth_token
