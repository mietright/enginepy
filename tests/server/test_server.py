from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Assuming enginepy.config.config() and enginepy.init.init exist and work as expected
# Import the specific items we need to test or mock
from enginepy.config import Config, ConfigSchema
from enginepy.server.server import CAgentsServer, serve


@pytest.fixture
def http_client(app: FastAPI) -> TestClient:
    """Fixture to create a TestClient instance for HTTP testing."""
    return TestClient(app)



def test_enginepy_server_config():
    """Verify the router and middleware configuration of CAgentsServer."""
    assert CAgentsServer._routers == {
        "enginepy.server.api.agents:router",
        "enginepy.server.api.job_info:router",
    }
    assert CAgentsServer._middlewares == {"tokenAuth"}


@patch("enginepy.server.server.config")
@patch("enginepy.server.server.serve_from_config")
@patch("enginepy.server.server.init")
def test_serve_function_calls(
    mock_init: MagicMock, mock_serve_from_config: MagicMock, mock_config: MagicMock
):
    """Verify that serve() calls config, serve_from_config, and init correctly."""
    # Arrange
    mock_app = MagicMock(spec=FastAPI)
    mock_serve_from_config.return_value = mock_app

    mock_config_obj = MagicMock(spec=Config)
    mock_config_schema = MagicMock(spec=ConfigSchema)
    mock_config_obj.conf = mock_config_schema  # Simulate accessing the .conf attribute
    mock_config.return_value = mock_config_obj

    # Act
    returned_app = serve()

    # Assert
    # Use assert_called_with because the reset_config fixture also calls config()
    mock_config.assert_called_with()
    mock_serve_from_config.assert_called_once_with(mock_config_obj, CAgentsServer)
    mock_init.assert_called_once_with(
        mock_config_schema, mode="server", extra={"app": mock_app}
    )
    assert returned_app is mock_app


def test_serve_integration_basic(http_client: TestClient): # Change fixture name here
    """
    Test that the server built by serve() starts and a basic route works.
    Uses the client fixture which relies on the app fixture from conftest.py.
    """
    # Make a request to a known simple endpoint (like version)
    response = http_client.get("/api/agents/version") # Use http_client fixture
    assert response.status_code == 200
    assert "version" in response.json()

    response_docs = http_client.get("/docs") # Use http_client
    assert response_docs.status_code == 200
