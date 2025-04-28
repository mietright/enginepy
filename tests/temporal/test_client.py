from unittest.mock import ANY, AsyncMock, MagicMock

import pytest
from temporalio.client import Client

from enginepy.config import Config, TemporalCustomConfigSchema

# Import the functions and classes to test
from enginepy.temporal.client import GTClient, TClient, tclient


@pytest.fixture(autouse=True)
def clear_tclient_cache():
    """Clears the GTClient instance before each test."""
    GTClient.reinit()
    yield
    GTClient.reinit()

@pytest.fixture
def mock_temporal_config(mocker) -> TemporalCustomConfigSchema:
    """Provides a mock TemporalCustomConfigSchema."""
    config_schema = TemporalCustomConfigSchema(
        host="mock-temporal:7233",
        namespace="mock-namespace",
    )
    # Mock the global config function to return our mock config
    mock_config_instance = MagicMock(spec=Config)
    mock_config_instance.temporalio = config_schema
    mocker.patch('enginepy.temporal.client.config', return_value=mock_config_instance)
    return config_schema

@pytest.fixture
def mock_client_connect(mocker) -> AsyncMock:
    """Mocks temporalio.client.Client.connect."""
    mock_connect = AsyncMock(spec=Client.connect)
    mock_client_instance = AsyncMock(spec=Client)
    mock_connect.return_value = mock_client_instance
    mocker.patch('temporalio.client.Client.connect', mock_connect)
    return mock_connect

# --- TClient Tests ---

@pytest.mark.asyncio
async def test_tclient_init_with_config(mock_temporal_config):
    """Test TClient initialization with a specific config."""
    custom_conf = TemporalCustomConfigSchema(host="custom:7233", namespace="custom")
    tc = TClient(conf=custom_conf)
    assert tc.conf == custom_conf
    assert tc._client is None

@pytest.mark.asyncio
async def test_tclient_init_without_config(mock_temporal_config):
    """Test TClient initialization uses global config if none provided."""
    tc = TClient()
    assert tc.conf == mock_temporal_config
    assert tc._client is None

@pytest.mark.asyncio
async def test_tclient_set_client(mock_temporal_config):
    """Test setting the client manually."""
    tc = TClient()
    mock_client = MagicMock(spec=Client)
    tc.set_client(mock_client)
    assert tc._client == mock_client

@pytest.mark.asyncio
async def test_tclient_client_connects_if_none(mock_temporal_config, mock_client_connect):
    """Test client() connects if _client is None."""
    tc = TClient()
    client_instance = await tc.client()

    mock_client_connect.assert_called_once_with(
        mock_temporal_config.host,
        namespace=mock_temporal_config.namespace,
        lazy=True,
        data_converter=ANY
    )
    assert client_instance == mock_client_connect.return_value
    assert tc._client == client_instance  # Check if client is stored

@pytest.mark.asyncio
async def test_tclient_client_returns_existing(mock_temporal_config, mock_client_connect):
    """Test client() returns existing client without reconnecting."""
    tc = TClient()
    mock_existing_client = MagicMock(spec=Client)
    tc.set_client(mock_existing_client)

    client_instance = await tc.client()

    assert client_instance == mock_existing_client
    mock_client_connect.assert_not_called()  # Should not connect again

# --- GTClient Tests (Singleton Behavior) ---

@pytest.mark.asyncio
async def test_gtclient_singleton(mock_temporal_config, mock_client_connect):
    """Test GTClient acts as a singleton."""
    gtc1 = GTClient()
    client1 = await gtc1.client()

    gtc2 = GTClient()  # Get instance again
    client2 = await gtc2.client()

    assert gtc1 is gtc2  # Should be the same TClient instance internally
    assert client1 is client2  # Should return the same client object
    mock_client_connect.assert_called_once()  # Connect should only be called once

@pytest.mark.asyncio
async def test_gtclient_reinit(mock_temporal_config, mock_client_connect):
    """Test GTClient reinitialization."""
    gtc1 = GTClient()
    await gtc1.client()  # First connection
    mock_client_connect.assert_called_once()

    GTClient.reinit()  # Reinitialize the singleton

    gtc2 = GTClient()  # Get a new instance after reinit
    await gtc2.client()  # Second connection attempt

    assert gtc1 is not gtc2  # The internal instance should be different now
    assert mock_client_connect.call_count == 2  # Connect should be called again

# --- tclient() Function Tests ---

@pytest.mark.asyncio
async def test_tclient_function(mock_temporal_config, mock_client_connect):
    """Test the global tclient() function uses the singleton."""
    client1 = await tclient()
    client2 = await tclient()  # Call again

    assert client1 is client2  # Should return the same client instance
    mock_client_connect.assert_called_once()  # Connect should only happen once

@pytest.mark.asyncio
async def test_tclient_function_with_config(mock_temporal_config, mock_client_connect):
    """Test tclient() with explicit config (though GTClient overrides this)."""
    custom_conf = TemporalCustomConfigSchema(host="ignored:7233")
    client1 = await tclient(conf=custom_conf)
    client2 = await tclient()

    assert client1 is client2
    mock_client_connect.assert_called_once_with(
        custom_conf.host, # The singleton was initialized with this host
        namespace=custom_conf.namespace, # The singleton was initialized with this namespace
        lazy=True,
        data_converter=ANY
    )
