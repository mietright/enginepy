from functools import cache

from enginepy.config import config
from enginepy.engine_client import EngineClient


@cache
def engine_client() -> EngineClient:
    """
    Creates and caches a EngineClient instance based on the current configuration.

    The `@cache` decorator memoizes the client instance. This means the client
    is created only once with the configuration values present during the first call.
    If the configuration (e.g., endpoint or token from `config()`) changes
    dynamically during the application's runtime *after* this function has been
    called, the cached client will still use the *old* configuration.

    To force the creation of a new client with updated configuration,
    clear the cache using `engine_client.cache_clear()`.

    Returns:
        A cached EngineClient instance.
    """
    cfg = config()
    return EngineClient(cfg.engine.endpoint, cfg.engine.token)
