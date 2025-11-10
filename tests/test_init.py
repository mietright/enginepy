from unittest.mock import MagicMock, patch

import pytest

from enginepy.config import ConfigSchema, LogfireConfigSchema
from enginepy.init import init, init_logfire


@pytest.fixture
def mock_logfire_config() -> LogfireConfigSchema:
    """Fixture for a LogfireConfigSchema with a token."""
    return LogfireConfigSchema(token="test-logfire-token")


@pytest.fixture
def mock_logfire_config_no_token() -> LogfireConfigSchema:
    """Fixture for a LogfireConfigSchema without a token."""
    return LogfireConfigSchema(token="")


@pytest.fixture
def mock_config(mock_logfire_config: LogfireConfigSchema) -> ConfigSchema:
    """Fixture for a main ConfigSchema."""
    cfg = ConfigSchema(app={"env": "test-env"})  # Uses defaults
    cfg.logfire = mock_logfire_config
    return cfg


@pytest.fixture
def mock_config_no_token(mock_logfire_config_no_token: LogfireConfigSchema) -> ConfigSchema:
    """Fixture for a main ConfigSchema with no logfire token."""
    cfg = ConfigSchema(app={"env": "test-env-no-token"})  # Uses defaults
    cfg.logfire = mock_logfire_config_no_token
    return cfg


@patch("enginepy.init.logfire")
def test_init_logfire_with_token(mock_logfire, mock_logfire_config: LogfireConfigSchema):
    """Test init_logfire when a token is provided."""
    extra = {"env": "dev"}
    init_logfire(mock_logfire_config, mode="worker", extra=extra)

    mock_logfire.configure.assert_called_once_with(token="test-logfire-token", environment="dev")
    mock_logfire.instrument_openai_agents.assert_called_once()
    mock_logfire.instrument_fastapi.assert_not_called()


@patch("enginepy.init.logfire")
def test_init_logfire_without_token(mock_logfire, mock_logfire_config_no_token: LogfireConfigSchema):
    """Test init_logfire when no token is provided."""
    init_logfire(mock_logfire_config_no_token, mode="worker", extra={})

    mock_logfire.configure.assert_not_called()
    mock_logfire.instrument_openai_agents.assert_not_called()
    mock_logfire.instrument_fastapi.assert_not_called()


@patch("enginepy.init.logfire")
def test_init_logfire_server_mode_with_app(mock_logfire, mock_logfire_config: LogfireConfigSchema):
    """Test init_logfire in server mode with an app provided."""
    mock_app = MagicMock()
    extra = {"env": "prod", "app": mock_app}
    init_logfire(mock_logfire_config, mode="server", extra=extra)

    mock_logfire.configure.assert_called_once_with(token="test-logfire-token", environment="prod")
    mock_logfire.instrument_openai_agents.assert_called_once()
    mock_logfire.instrument_fastapi.assert_called_once_with(
        mock_app, capture_headers=True, excluded_urls=[".*/docs", ".*/redoc", ".*/metrics", ".*/health"]
    )


@patch("enginepy.init.logfire")
def test_init_logfire_server_mode_without_app(mock_logfire, mock_logfire_config: LogfireConfigSchema):
    """Test init_logfire in server mode without an app provided."""
    extra = {"env": "staging"} # No 'app' key
    init_logfire(mock_logfire_config, mode="server", extra=extra)

    mock_logfire.configure.assert_called_once_with(token="test-logfire-token", environment="staging")
    mock_logfire.instrument_openai_agents.assert_called_once()
    mock_logfire.instrument_fastapi.assert_not_called()


@patch("enginepy.init.init_logfire")
def test_init_calls_init_logfire(mock_init_logfire, mock_config: ConfigSchema):
    """Test that init calls init_logfire with correct arguments."""
    extra_in = {"some_key": "some_value"}
    init(mock_config, mode="server", extra=extra_in)

    # Check that the original extra dict was modified
    assert "env" in extra_in
    assert extra_in["env"] == "test-env"

    # Check that init_logfire was called with the modified extra dict
    mock_init_logfire.assert_called_once_with(mock_config.logfire, "server", extra_in)


@patch("enginepy.init.init_logfire")
def test_init_handles_none_extra(mock_init_logfire, mock_config: ConfigSchema):
    """Test that init handles extra=None correctly."""
    init(mock_config, mode="worker", extra=None)

    expected_extra = {"env": "test-env"}
    mock_init_logfire.assert_called_once_with(mock_config.logfire, "worker", expected_extra)


@patch("enginepy.init.init_logfire")
def test_init_uses_config_env(mock_init_logfire, mock_config: ConfigSchema):
    """Test that init correctly extracts env from config."""
    init(mock_config, mode="worker") # extra defaults to None

    expected_extra = {"env": "test-env"}
    mock_init_logfire.assert_called_once_with(mock_config.logfire, "worker", expected_extra)
