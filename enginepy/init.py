from typing import Any, Literal

import logfire

from enginepy.config import ConfigSchema, LogfireConfigSchema


def init_logfire(
    config: LogfireConfigSchema, mode: Literal["server", "worker"] = "server", extra: dict[str, Any] | None = None
):
    if config.token:
        if not extra:
            extra = {}
        logfire.configure(token=config.token, environment=extra.get("env", "dev"))
        logfire.instrument_openai_agents()
        if mode == "server" and extra is not None and extra.get("app"):
            app = extra["app"]
            logfire.instrument_fastapi(
                app, capture_headers=True, excluded_urls=[".*/docs", ".*/redoc", ".*/metrics", ".*/health"]
            )


def init(config: ConfigSchema, mode: Literal["server", "worker"] = "server", extra: dict[str, Any] | None = None):
    if not extra:
        extra = {}
    extra["env"] = config.app.env
    init_logfire(config.logfire, mode, extra)
