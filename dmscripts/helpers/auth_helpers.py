import os

DEV_ALIASES = ('dev', 'development', 'local')


def get_auth_token(api, stage):
    if stage.lower() in DEV_ALIASES:
        return 'myToken'

    env_var_api_name = 'data-api' if api == 'api' else api
    env_var_api_name = env_var_api_name.replace('-', '_')
    env_var = "DM_{}_TOKEN_{}".format(env_var_api_name.upper(), stage.upper())

    try:
        auth_token = os.environ[env_var]
    except KeyError:
        raise RuntimeError(
            "Unable to find api token in environment."
            " Please ensure that ${} has been exported correctly.".format(env_var))

    return auth_token


def get_api_url(api, stage):
    if stage in DEV_ALIASES:
        url = 'http://localhost:{}'.format(5001 if api == 'search-api' else 5000)
    elif stage == 'production':
        url = 'https://{}.digitalmarketplace.service.gov.uk'
    else:
        url = 'https://{{}}.{}.marketplace.team'.format(stage)

    return url.format(api)
