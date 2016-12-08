import pytest
from mock import Mock


@pytest.fixture
def mock_data_client():
    mock_data_client = Mock()
    mock_data_client.get_framework.return_value = dict(frameworks=dict(lots=[
        {'slug': 'test_lot_slug_1'},
        {'slug': 'test_lot_slug_2'},
    ]))
    return mock_data_client

