

from enginepy.clients import engine_client
from enginepy.config import config
from enginepy.engine_client import EngineClient


def test_engine_client_creation_and_cache():
    """
    Test that engine_client() creates an EngineClient instance
    and that the instance is cached.
    """
    # Ensure config is loaded from the test file
    cfg = config(reload=True) # Use reload to ensure test config is active
    expected_endpoint = cfg.engine.endpoint
    expected_token = cfg.engine.token

    # First call - should create and cache the client
    client1 = engine_client()
    assert isinstance(client1, EngineClient)
    assert client1.endpoint.geturl() == expected_endpoint # Use .geturl() to get the string URL
    assert client1.token == expected_token

    # Second call - should return the cached instance
    client2 = engine_client()
    assert client1 is client2 # Check if it's the exact same object instance

    # Clear cache for subsequent tests if needed, though fixture should handle it
    engine_client.cache_clear()


def test_engine_client_cache_clear():
    """
    Test that clearing the cache results in a new client instance.
    """
    client1 = engine_client()

    engine_client.cache_clear()

    # Second call after clearing cache - should be a new instance
    client2 = engine_client()

    assert isinstance(client2, EngineClient)
    assert client1 is not client2 # Should be a different object instance

    engine_client.cache_clear()


# Optional: Test that configuration changes after initial call are ignored due to cache
def test_engine_client_ignores_config_changes_after_cache(monkeypatch):
    """
    Test that the cached client uses the config from the first call,
    even if the underlying config changes later.
    """
    # Initial call with test config
    client1 = engine_client()
    original_token = client1.token

    # Simulate config change (e.g., via environment variables)
    new_token = "new-test-token-xyz"
    monkeypatch.setenv("ENGINEPY_ENGINE__TOKEN", new_token)
    # Reload config *object* but don't clear the function cache
    _ = config(reload=True)
    assert config().engine.token == new_token # Verify config object updated

    # Call engine_client again - should still return the *cached* client
    client2 = engine_client()

    assert client1 is client2 # Still the same instance
    assert client2.token == original_token # Token remains the original one due to cache

    engine_client.cache_clear()
    monkeypatch.delenv("ENGINEPY_ENGINE__TOKEN", raising=False)
    _ = config(reload=True) # Reload original config
