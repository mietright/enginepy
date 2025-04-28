import os

from enginepy.config import Config, EngineConfigSchema, LogfireConfigSchema, config


def test_config_test_env():
    assert config().app.env == "test"


def test_config_fields():
    assert config().sentry.dsn is None
    assert config().logging.level == "info"
    assert config().conf.app.env == "test"
    assert config().conf.name == "enginepy-test"


def test_config_reinit():
    conf = config().dump()
    _ = config(reload=True)
    assert config().dump() == conf
    # Changes are ignored without reinit
    config("tests/data/config-2.yaml")
    assert config().dump() == conf
    # Changes are applied after reinit
    config("tests/data/config-2.yaml", reload=True)
    assert config().dump() != conf




def test_config_env_precedence(monkeypatch):
    assert config(reload=True).app.env == "test"
    monkeypatch.setattr(
        os, "environ", {"ENGINEPY_APP__ENV": "test-3", "ENGINEPY_CONFIG": "tests/data/test_config.yaml"}
    )
    # Env setting has precedence over config file
    assert config(reload=True).app.env == "test-3"
    # Other env are not affected
    assert config().conf.name == "enginepy-test"
    monkeypatch.setattr(
        os, "environ", {"ENGINEPY_NAME": "enginepy-test-3", "ENGINEPY_CONFIG": "tests/data/test_config.yaml"}
    )
    assert config(reload=True).conf.name == "enginepy-test-3"
    assert config(reload=True).conf.app.env == "test"


def test_config_path_failed_path_fallback():
    config("tests/data/config-dontexist.yaml", reload=True)
    assert config().app.env == "dev"


def test_config_property_accessors():
    """Test accessing config properties like logfire and engine."""
    cfg: Config = config()
    # Accessing the properties covers the getter methods
    logfire_conf = cfg.logfire
    engine_conf = cfg.engine
    assert isinstance(logfire_conf, LogfireConfigSchema)
    assert isinstance(engine_conf, EngineConfigSchema)
    # Optionally, check a value from the test config
    assert engine_conf.token == "sometesttoken" # Corrected token value from test_config.yaml
