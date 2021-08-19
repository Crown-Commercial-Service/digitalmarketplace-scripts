import pytest
import mock
from dmscripts.generate_database_data import (
    open_gcloud_12,
    make_gcloud_12_live,
    create_buyer_email_domain_if_not_present,
    G_CLOUD_FRAMEWORK,
    generate_user,
    set_all_frameworks_to_expired,
    USER_ROLES,
)


class TestGenerateDataBase:

    def setup_method(self, method):
        self.api_client_patch = mock.patch("dmapiclient.DataAPIClient", autospec=True)
        self.api_client = self.api_client_patch.start()

    def teardown_method(self, method):
        self.api_client_patch.stop()


class TestGenerateUser(TestGenerateDataBase):

    def test_generate_user_has_correct_keys(self):
        buyer = generate_user(data=self.api_client, role="buyer")
        assert buyer.keys() == {"name", "emailAddress", "password", "role"}

    @pytest.mark.parametrize("role", [role for role in USER_ROLES])
    def test_generate_user_allows_valid_roles(self, role):
        generate_user(self.api_client, role=role)

    def test_generate_user_doesnt_allow_invalid_role(self):
        with pytest.raises(ValueError):
            generate_user(self.api_client, role="not-a-role")


class TestBuyerEmailDomain(TestGenerateDataBase):

    def test_adds_domain(self):
        create_buyer_email_domain_if_not_present(data=self.api_client, email_domain="user.marketplace.team")
        self.api_client.create_buyer_email_domain.assert_called_with("user.marketplace.team")

    def test_doesnt_add_domain_twice(self):
        self.api_client.get_buyer_email_domains_iter.return_value = [{"domainName": "user.marketplace.team", "id": 1}]
        create_buyer_email_domain_if_not_present(data=self.api_client, email_domain="user.marketplace.team")
        assert not self.api_client.create_buyer_email_domain.called


class TestSetFrameworksToExpired(TestGenerateDataBase):

    def test_set_all_frameworks_to_expired(self):
        self.api_client.find_frameworks.return_value = {"frameworks": [
            {
                "slug": "g-cloud-6",
                "status": "live"
            },
            {
                "slug": "g-cloud-7",
                "status": "live"
            },
            {
                "slug": "g-cloud-5",
                "status": "expired"
            },
        ]}
        set_all_frameworks_to_expired(self.api_client)
        assert self.api_client.update_framework.call_count == 2
        self.api_client.update_framework.assert_any_call("g-cloud-6", {"status": "expired"})
        self.api_client.update_framework.assert_any_call("g-cloud-7", {"status": "expired"})


class TestOpenGCloud12(TestGenerateDataBase):

    def test_passed_valid_data(self):
        open_gcloud_12(self.api_client)
        self.api_client.create_framework.assert_called_with(
            slug=G_CLOUD_FRAMEWORK["slug"],
            name=G_CLOUD_FRAMEWORK["name"],
            framework_family_slug=G_CLOUD_FRAMEWORK["family"],
            lots=[lot["slug"] for lot in G_CLOUD_FRAMEWORK["lots"]],
            has_further_competition=False,
            has_direct_award=True,
            status="open"
        )
        self.api_client.update_framework.assert_called_with(
            framework_slug=G_CLOUD_FRAMEWORK["slug"],
            data={
                "clarificationQuestionsOpen": True
            }
        )

    def test_doesnt_add_gcloud_if_already_present(self):
        self.api_client.find_frameworks.return_value = {
            "frameworks": [
                {
                    "slug": G_CLOUD_FRAMEWORK["slug"]
                }
            ]
        }
        open_gcloud_12(self.api_client)
        assert not self.api_client.create_framework.called

        self.api_client.update_framework.assert_called_with(
            framework_slug=G_CLOUD_FRAMEWORK["slug"],
            data={
                "clarificationQuestionsOpen": True
            }
        )


class TestMakeGCloud12Live(TestGenerateDataBase):

    def test_update_framework_is_called(self):
        make_gcloud_12_live(self.api_client)
        self.api_client.update_framework.assert_called_with(
            framework_slug=G_CLOUD_FRAMEWORK["slug"],
            data={
                "status": "live",
                "clarificationQuestionsOpen": False
            }
        )
