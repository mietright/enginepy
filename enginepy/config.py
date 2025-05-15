# pylint: disable=no-self-argument
import logging
from typing import Any

import ant31box.config
from ant31box.config import BaseConfig, GConfig, LoggingConfigSchema, SentryConfigSchema
from pydantic import Field
from pydantic_settings import SettingsConfigDict

LOGGING_CONFIG: dict[str, Any] = ant31box.config.LOGGING_CONFIG
LOGGING_CONFIG["loggers"].update({"root": {"handlers": ["default"], "level": "DEBUG", "propagate": True}})

logger: logging.Logger = logging.getLogger("enginepy")


class LoggingCustomConfigSchema(LoggingConfigSchema):
    log_config: dict[str, Any] | str | None = Field(default_factory=lambda: LOGGING_CONFIG)


class LogfireConfigSchema(BaseConfig):
    token: str = Field(default="")


class EngineConfigSchema(BaseConfig):
    token: str = Field(default="changeme")
    endpoint: str = Field(default="https://engine.stg.conny.dev")


ENVPREFIX = "ENGINEPY"


# Main configuration schema
class ConfigSchema(ant31box.config.ConfigSchema):
    model_config = SettingsConfigDict(
        env_prefix=f"{ENVPREFIX}_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="allow",
    )
    name: str = Field(default="enginepy")
    logfire: LogfireConfigSchema = Field(default_factory=LogfireConfigSchema)
    engine: EngineConfigSchema = Field(default_factory=EngineConfigSchema)


class Config(ant31box.config.GenericConfig[ConfigSchema]):
    _env_prefix = ENVPREFIX
    __config_class__ = ConfigSchema

    @property
    def logfire(self) -> LogfireConfigSchema:
        return self.conf.logfire

    @property
    def engine(self) -> EngineConfigSchema:
        return self.conf.engine

    @property
    def sentry(self) -> SentryConfigSchema:
        return self.conf.sentry


def config(path: str | None = None, reload: bool = False) -> Config:
    GConfig[Config].set_conf_class(Config)
    if reload:
        GConfig[Config].reinit()
    GConfig[Config](path)
    return GConfig[Config].instance()
