import pytest
import mock
from dmscripts.models.modeltrawler import ModelTrawler


class FakeClient:

    def find_fake_table_iter(self):
        return True


class TestModelTrawlerInit:

    def test_correct_initiation(self):
        mt = ModelTrawler('fake_table', FakeClient())
        assert mt.model == 'fake_table'
        assert mt.model_iter_method == 'find_fake_table_iter'

    def test_cannot_initiate_with_incorrect_model_name(self):
        with pytest.raises(AttributeError):
            ModelTrawler('real_table', FakeClient())

    def test_get_allowed_models_returns_allowed_models(self):
        mt = ModelTrawler('fake_table', FakeClient())
        assert set(mt._get_allowed_models()) == set(['fake_table'])


class TestModelTrawlerMethods:

    model_data = (
        {
            'id': 1,
            'name': 'Super cloud brief',
            'supplier': {'id': 100, 'name': 'Super cloud supplier'},
            'users': [{'id': 101, 'emailAddress': 'user@gov.uk', 'name': 'Super cloud user'}]
        }, {
            'id': 2,
            'name': 'Super cloud brief 2',
            'supplier': {'id': 200, 'name': 'Super cloud supplier 2'},
            'users': [{'id': 201, 'emailAddress': 'user2@gov.uk', 'name': 'Super cloud user 2'}]
        }
    )

    def test_filter_keys(self):
        keys = (
            'id',
            ('supplier', 'name'),
            ('users', 0, 'emailAddress')
        )

        initial_model_dict = self.model_data[0].copy()

        expected_model_dict = {
            'id': 1,
            'supplier.name': 'Super cloud supplier',
            'users.0.emailAddress': 'user@gov.uk'
        }

        mt = ModelTrawler('fake_table', FakeClient())
        assert mt._filter_keys(keys)(initial_model_dict) == expected_model_dict

    def test_get_data(self):
        keys = (
            'id',
            ('users', 0, 'emailAddress')
        )

        expected_model_data = (
            {'id': 1, 'users.0.emailAddress': 'user@gov.uk'},
            {'id': 2, 'users.0.emailAddress': 'user2@gov.uk'}
        )

        with mock.patch.object(FakeClient, 'find_fake_table_iter', return_value=iter(self.model_data)):
            mt = ModelTrawler('fake_table', FakeClient())
            assert tuple(mt.get_data(keys)) == expected_model_data

    def test_get_data_with_limit(self):
        keys = (
            'id',
            ('users', 0, 'emailAddress')
        )

        expected_model_data = ({'id': 1, 'users.0.emailAddress': 'user@gov.uk'},)

        with mock.patch.object(FakeClient, 'find_fake_table_iter', return_value=iter(self.model_data)):
            mt = ModelTrawler('fake_table', FakeClient())
            assert tuple(mt.get_data(keys, limit=1)) == expected_model_data

    def test_get_data_with_kwargs(self):
        _kwargs = {
            'something_true': True,
            'something_false': False
        }

        with mock.patch.object(
            FakeClient, 'find_fake_table_iter', return_value=(m for m in ({'id': 1}, {'id': 2}))
        ) as mock_method:
            mt = ModelTrawler('fake_table', FakeClient())
            list(mt.get_data(('id',), limit=1, **_kwargs))
            # note that `limit` isn't included as a keyword argument
            mock_method.assert_called_once_with(something_true=True, something_false=False)
