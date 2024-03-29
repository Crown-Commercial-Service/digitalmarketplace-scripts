import os
import subprocess
import yaml

DEV_ALIASES = ('dev', 'development', 'local')

STAGE_TO_FILE = {
    'pre': 'preview',
    'stg': 'staging'
}


def _decrypt_yaml_file_with_sops(credentials_repo_path, credentials_filename):
    creds_output = subprocess.check_output([
        "{}/sops-wrapper".format(credentials_repo_path),
        "-d",
        "{}/{}".format(credentials_repo_path, credentials_filename)
    ])
    return yaml.safe_load(creds_output)


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
        creds_json = _decrypt_yaml_file_with_sops(
            DM_CREDENTIALS_REPO,
            f"vars/{STAGE_TO_FILE[stage] if stage in STAGE_TO_FILE else stage}.yaml",
        )
        auth_tokens = creds_json[api]['auth_tokens']
        auth_token = next(token for token in auth_tokens if token.startswith(token_prefix))

    return auth_token


def _get_nested_value(creds_json, env_var_path_list):
    """
    Handle nested values in the credentials json.
    :param creds_json: e.g. {"performance_platform_bearer_tokens": {"g-cloud": "myToken"}}
    :param env_var_path_list: e.g. ["performance_platform_bearer_tokens", "g-cloud"]
    :return: e.g. "myToken"
    """
    if len(env_var_path_list) > 1:
        return _get_nested_value(creds_json.get(env_var_path_list[0], {}), env_var_path_list[1:])
    return creds_json.get(env_var_path_list[0])


def get_jenkins_env_variable_from_credentials(env_var_dot_path, require_jenkins_user=True):
    """
    Scripts run on Jenkins can retrieve a variable from the Jenkins vars
    env_var_dot_path: a dot separated string, e.g. "jenkins_env_variables.NOTIFY_API_TOKEN"
    """
    if require_jenkins_user and subprocess.check_output(["whoami"]) != 'jenkins':
        raise ValueError("Only Jenkins user can retrieve this value")

    DM_CREDENTIALS_REPO = os.environ.get('DM_CREDENTIALS_REPO', '../digitalmarketplace-credentials')
    creds_json = _decrypt_yaml_file_with_sops(DM_CREDENTIALS_REPO, 'jenkins-vars/jenkins.yaml')

    return _get_nested_value(creds_json, env_var_dot_path.split('.'))


def get_jenkins_env_variable(jenkins_var_name, require_jenkins_user=True):
    # Check the local env first, otherwise decrypt from credentials
    value = os.environ.get(jenkins_var_name)

    if not value:
        value = get_jenkins_env_variable_from_credentials(
            "jenkins_env_variables.{}".format(jenkins_var_name),
            require_jenkins_user=require_jenkins_user
        )

    return value


def get_mailchimp_credentials(stage):
    credentials_repo = os.environ.get('DM_CREDENTIALS_REPO', '../digitalmarketplace-credentials')
    credentials = _decrypt_yaml_file_with_sops(credentials_repo, f"vars/{stage}.yaml")
    return (
        credentials['supplier_frontend']['mailchimp_username'],
        credentials['supplier_frontend']['mailchimp_api_key']
    )
