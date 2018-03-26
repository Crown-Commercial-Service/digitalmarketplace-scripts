import os
import subprocess
import yaml

DEV_ALIASES = ('dev', 'development', 'local')


def get_auth_token(api, stage):
    if stage.lower() in DEV_ALIASES:
        return 'myToken'

    env_var = "DM_{}_TOKEN_{}".format(api.upper(), stage.upper())
    auth_token = os.environ.get(env_var)

    if not auth_token:
        DM_CREDENTIALS_REPO = os.environ.get('DM_CREDENTIALS_REPO', '../digitalmarketplace-credentials')
        token_prefix = 'J' if subprocess.check_output(["whoami"]) == 'jenkins' else 'D'
        creds = subprocess.check_output([
            "{}/sops-wrapper".format(DM_CREDENTIALS_REPO),
            "-d",
            "{}/vars/{}.yaml".format(DM_CREDENTIALS_REPO, stage)
        ])
        auth_tokens = yaml.load(creds)[api]['auth_tokens']
        auth_token = next(token for token in auth_tokens if token.startswith(token_prefix))

    return auth_token


def get_api_url(api, stage):
    if stage in DEV_ALIASES:
        url = 'http://localhost:{}'.format(5001 if api == 'search-api' else 5000)
    elif stage == 'production':
        url = 'https://{}.digitalmarketplace.service.gov.uk'
    else:
        url = 'https://{{}}.{}.marketplace.team'.format(stage)

    return url.format(api)
