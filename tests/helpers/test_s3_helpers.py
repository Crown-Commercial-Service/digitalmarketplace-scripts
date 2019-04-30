import pytest
from dmscripts.helpers.s3_helpers import get_bucket_name


class TestGetBucketName:

    @pytest.mark.parametrize(
        'stage, expected_bucket_name',
        [
            ('local', 'digitalmarketplace-dev-uploads'),
            ('dev', 'digitalmarketplace-dev-uploads'),
            ('preview', 'digitalmarketplace-agreements-preview-preview'),
            ('staging', 'digitalmarketplace-agreements-staging-staging'),
            ('production', 'digitalmarketplace-agreements-production-production'),
        ]
    )
    def test_get_bucket_name_for_agreements_documents(self, stage, expected_bucket_name):
        assert get_bucket_name(stage, 'agreements') == expected_bucket_name

    def test_get_bucket_name_returns_none_for_invalid_stage(self):
        assert get_bucket_name('xanadu', 'agreements') is None

    def test_get_bucket_name_returns_none_for_invalid_bucket_category(self):
        assert get_bucket_name('local', 'bananas') is None
