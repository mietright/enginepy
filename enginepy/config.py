# pylint: disable=no-self-argument
import logging
from typing import Any

import ant31box.config
from ant31box.config import BaseConfig, FastAPIConfigSchema, GConfig, LoggingConfigSchema
from pydantic import Field
from pydantic_settings import SettingsConfigDict
from temporalloop.config_loader import TemporalConfigSchema, TemporalScheduleSchema, WorkerConfigSchema

LOGGING_CONFIG: dict[str, Any] = ant31box.config.LOGGING_CONFIG
LOGGING_CONFIG["loggers"].update({"enginepy": {"handlers": ["default"], "level": "INFO", "propagate": True}})

logger: logging.Logger = logging.getLogger("enginepy")


class LoggingCustomConfigSchema(LoggingConfigSchema):
    log_config: dict[str, Any] | str | None = Field(default_factory=lambda: LOGGING_CONFIG)


class AntbedConfigSchema(BaseConfig):
    token: str = Field(default="changeme")
    endpoint: str = Field(default="http://localhost:7080")


class LogfireConfigSchema(BaseConfig):
    token: str = Field(default="")


class FastAPIConfigCustomSchema(FastAPIConfigSchema):
    server: str = Field(default="enginepy.server.server:serve")


class OpenAIProjectKeySchema(BaseConfig):
    api_key: str = Field(default="enginepy-openaiKEY")
    project_id: str = Field(default="proj-1xZoR")
    name: str = Field(default="default")
    url: str | None = Field(default=None)


class OpenAIConfigSchema(BaseConfig):
    organization: str = Field(default="Ant31")
    organization_id: str = Field(default="org-1xZoRaUM")
    url: str | None = Field(default=None)
    projects: list[OpenAIProjectKeySchema] = Field(
        default=[
            OpenAIProjectKeySchema(
                api_key="enginepy-openaiKEY",
                project_id="proj_OIMUS8HgaQZ",
                name="openai",
            ),
            OpenAIProjectKeySchema(
                api_key="enginepy-openaiKEY",
                project_id="proj_NrZHbXS1CDXh",
                name="gemini",
                url="https://generativelanguage.googleapis.com/v1beta/openai/",
            ),
        ]
    )

    def get_project(self, name: str) -> OpenAIProjectKeySchema | None:
        for project in self.projects:
            if project.name.lower() == name.lower():
                return project
        return None


class TemporalCustomConfigSchema(TemporalConfigSchema):
    workers: list[WorkerConfigSchema] = Field(
        default=[
            WorkerConfigSchema(
                name="enginepy",
                queue="enginepy-queue",
                interceptors=["temporalio.contrib.opentelemetry:TracingInterceptor"],
                activities=[
                    "enginepy.temporal.activities:echo",
                    "enginepy.temporal.activities:agent_summary",
                ],
                workflows=[
                    "enginepy.temporal.workflows.echo:EchoWorkflow",
                    "enginepy.temporal.workflows.summary:AgentSummaryWorkflow",
                ],
            ),
        ],
    )
    converter: str | None = Field(default="temporalio.contrib.pydantic:pydantic_data_converter")


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
    openai: OpenAIConfigSchema = Field(default_factory=OpenAIConfigSchema)
    logging: LoggingConfigSchema = Field(default_factory=LoggingCustomConfigSchema, exclude=True)
    server: FastAPIConfigSchema = Field(default_factory=FastAPIConfigCustomSchema)
    temporalio: TemporalCustomConfigSchema = Field(default_factory=TemporalCustomConfigSchema)
    schedules: dict[str, TemporalScheduleSchema] = Field(default_factory=dict, exclude=True)
    antbed: AntbedConfigSchema = Field(default_factory=AntbedConfigSchema)


class Config(ant31box.config.Config[ConfigSchema]):
    _env_prefix = ENVPREFIX
    __config_class__: type[ConfigSchema] = ConfigSchema

    @property
    def openai(self) -> OpenAIConfigSchema:
        return self.conf.openai

    @property
    def logfire(self) -> LogfireConfigSchema:
        return self.conf.logfire

    @property
    def temporalio(self) -> TemporalCustomConfigSchema:
        return self.conf.temporalio

    @property
    def schedules(self) -> dict[str, TemporalScheduleSchema]:
        return self.conf.schedules

    @property
    def antbed(self) -> AntbedConfigSchema:
        return self.conf.antbed


def config(path: str | None = None, reload: bool = False) -> Config:
    GConfig[Config].set_conf_class(Config)
    if reload:
        GConfig[Config].reinit()
    # load the configuration
    GConfig[Config](path)
    # Return the instance of the configuration
    return GConfig[Config].instance()
