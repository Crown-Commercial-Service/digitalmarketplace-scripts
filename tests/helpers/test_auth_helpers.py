import os
import mock
import pytest

from dmscripts.helpers.auth_helpers import get_jenkins_env_variable_from_credentials, get_jenkins_env_variable


@mock.patch.dict(os.environ, {'DM_CREDENTIALS_REPO': '/path/to/credentials'})
@mock.patch('dmscripts.helpers.auth_helpers._decrypt_yaml_file_with_sops')
class TestGetJenkinsEnvVariablesFromCredentials:

    @pytest.mark.parametrize(
        'decrypted_json, var_path', [
            ({"foo": {"bar": "hurray"}}, "foo.bar"),
            ({"foo": "hurray"}, "foo"),
        ]
    )
    def test_get_jenkins_env_variable_from_credentials_decrypts_nested_yaml(
        self, decrypt_yaml_file_with_sops, decrypted_json, var_path
    ):
        decrypt_yaml_file_with_sops.return_value = decrypted_json

        assert get_jenkins_env_variable_from_credentials(var_path, require_jenkins_user=False) == "hurray"
        assert decrypt_yaml_file_with_sops.call_args_list == [
            mock.call("/path/to/credentials", "jenkins-vars/jenkins.yaml")
        ]

    @pytest.mark.parametrize(
        'decrypted_json', [
            {"foo": {"boo": "hurray"}},
            {"bar": "foo"},
            {},
        ]
    )
    def test_get_jenkins_env_variable_from_credentials_handles_nonexistent_path(
        self, decrypt_yaml_file_with_sops, decrypted_json
    ):
        decrypt_yaml_file_with_sops.return_value = decrypted_json

        assert get_jenkins_env_variable_from_credentials('foo.bar', require_jenkins_user=False) is None
        assert decrypt_yaml_file_with_sops.call_args_list == [
            mock.call("/path/to/credentials", "jenkins-vars/jenkins.yaml")
        ]

    @mock.patch('subprocess.check_output')
    def test_get_jenkins_env_variable_from_credentials_checks_for_jenkins_user(
        self, check_whoami_output, decrypt_yaml_file_with_sops
    ):
        decrypt_yaml_file_with_sops.return_value = {"foo": {"bar": "hurray"}}
        check_whoami_output.return_value = 'jenkins'

        get_jenkins_env_variable_from_credentials('foo.bar', require_jenkins_user=True)
        assert decrypt_yaml_file_with_sops.call_args_list == [
            mock.call("/path/to/credentials", "jenkins-vars/jenkins.yaml")
        ]

    @mock.patch('subprocess.check_output')
    def test_get_jenkins_env_variable_from_credentials_raises_if_not_jenkins_user(self, check_whoami_output, _):
        check_whoami_output.return_value = 'some other user'

        with pytest.raises(ValueError) as excinfo:
            get_jenkins_env_variable_from_credentials('foo.bar', require_jenkins_user=True)
        assert str(excinfo.value) == "Only Jenkins user can retrieve this value"


@mock.patch('dmscripts.helpers.auth_helpers.get_jenkins_env_variable_from_credentials')
class TestGetJenkinsEnvVariables:

    @mock.patch.dict(os.environ, {'MY_VAR': "I was hiding in the env all along"})
    def test_get_jenkins_env_variable_looks_in_os_environ_first(self, get_var_from_creds):
        assert get_jenkins_env_variable("MY_VAR") == "I was hiding in the env all along"
        assert get_var_from_creds.called is False

    @mock.patch.dict(os.environ, {'NOT_MY_VAR': "Nothing to see here mate"})
    def test_get_jenkins_env_variable_uses_creds_file_if_not_in_os_environ(self, get_var_from_creds):
        assert get_jenkins_env_variable("MY_VAR") == get_var_from_creds.return_value
        assert get_var_from_creds.call_args_list == [
            mock.call('jenkins_env_variables.MY_VAR', require_jenkins_user=True)
        ]
