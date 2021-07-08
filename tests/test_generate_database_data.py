import pytest
import mock
from dmscripts.generate_database_data import generate_user, USER_ROLES


class TestGenerateUser:

    def setup_method(self, method):
        self.api_client_patch = mock.patch("dmapiclient.DataAPIClient", autospec=True)
        self.api_client = self.api_client_patch.start()

    def teardown_method(self, method):
        self.api_client_patch.stop()

    def test_generate_user_has_correct_keys(self):
        buyer = generate_user(data=self.api_client, role="buyer")
        assert set(buyer.keys()) == {"name", "email_address", "password", "role"}

    @pytest.mark.parametrize("role", [role for role in USER_ROLES])
    def test_generate_user_allows_valid_roles(self, role):
        generate_user(self.api_client, role=role)

    def test_generate_user_doesnt_allow_invalid_role(self):
        with pytest.raises(ValueError):
            generate_user(self.api_client, role="not-a-role")
