from functools import cache

import logfire
from agents import set_tracing_export_api_key
from google import genai
from openai import AsyncOpenAI, OpenAI

from enginepy.antbed_client import AntbedClient
from enginepy.config import config


def set_tracing():
    openai = config().openai.get_project("openai")
    if openai is not None:
        print("set_Tracing")
        set_tracing_export_api_key(openai.api_key)


@cache
def openai_client(project_name: str = "") -> OpenAI:
    """Create a OpenAI instance with the given api_key
    It cache the answer for the same api_key
    use openai.cache_clear() to clear the cache
    """
    if not project_name:
        project = config().openai.projects[0]
    else:
        project = getattr(config().openai.projects, project_name)
    openaiconf = config().openai
    api_key = project.api_key
    organization = openaiconf.organization_id
    base_url = openaiconf.url
    client = OpenAI(
        api_key=api_key,
        organization=organization,
        project=project.project_id,
        base_url=base_url,
    )
    logfire.instrument_openai(client)
    return client


@cache
def openai_aclient(project_name: str = "") -> AsyncOpenAI:
    """Create a OpenAI instance with the given api_key
    It cache the answer for the same api_key
    use openai.cache_clear() to clear the cache
    """
    if not project_name:
        project = config().openai.projects[0]
    else:
        project = config().openai.get_project(project_name)
        if project is None:
            raise ValueError(f"Project {project_name} not found")
    set_tracing()
    openaiconf = config().openai
    api_key = project.api_key
    organization = openaiconf.organization_id
    base_url = project.url

    client = AsyncOpenAI(
        api_key=api_key,
        organization=organization,
        project=project.project_id,
        base_url=base_url,
    )
    logfire.instrument_openai(client)
    return client


@cache
def genai_client(project_name: str = "gemini") -> genai.Client:
    """Create a GenAI instance with the given api_key
    It cache the answer for the same api_key
    use genai.cache_clear() to clear the cache
    """
    project = config().openai.get_project(project_name)
    if project is None:
        raise ValueError(f"Project {project_name} not found")
    api_key = project.api_key
    set_tracing()
    return genai.Client(api_key=api_key)


@cache
def antbed_client() -> AntbedClient:
    """Create a AntbedClient instance
    It cache the answer for the same endpoint and token
    use antbed_client.cache_clear() to clear the cache
    """
    return AntbedClient(config().antbed.endpoint, config().antbed.token)
