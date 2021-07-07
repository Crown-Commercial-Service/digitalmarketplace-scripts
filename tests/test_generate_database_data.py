import pytest
import mock
from dmscripts.generate_database_data import generate_user, USER_ROLES

TEST_ROLES = USER_ROLES + ["not-a-role"]


class TestGenerateUser:

    def setup_method(self, method):
        self.api_client_patch = mock.patch("dmapiclient.DataAPIClient", autospec=True)
        self.api_client = self.api_client_patch.start()

    def teardown_method(self, method):
        self.api_client_patch.stop()

    def test_generate_user_has_correct_keys(self):
        buyer = generate_user(data=self.api_client, role="buyer")
        assert set(buyer.keys()) == {"name", "email_address", "password", "role"}

    @pytest.mark.parametrize(
        "role,expected_error", [(role, None if role in USER_ROLES else ValueError) for role in TEST_ROLES])
    def test_generate_user_validates_roles(self, role, expected_error):
        if expected_error is not None:
            with pytest.raises(expected_error):
                generate_user(self.api_client, role=role)

        else:
            generate_user(self.api_client, role=role)
