# pylint: disable=broad-exception-caught
# pylint: disable=too-many-locals
import asyncio
import inspect
import json
import logging
from collections.abc import Callable
from enum import StrEnum
from inspect import Parameter, Signature
from typing import Annotated, Any, get_args, get_origin

import pydantic
import typer
import yaml
from aiohttp import ClientResponseError
from ant31box.cmd.typer.default_config import app as default_config_app
from rich.console import Console
from rich.table import Table

# Import the actual config loader
from enginepy.config import config

# Import the client and models
from enginepy.engine_client import API_ENDPOINT_METADATA, EngineClient
from enginepy.models import ApiEndpoint

logger = logging.getLogger(__name__)


# --- Helper Functions for Type Validation ---


def _parse_json_value(param_name: str, value_str: str) -> Any:
    """Helper to parse JSON string, raising ValueError on failure."""
    try:
        return json.loads(value_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON provided for '{param_name}': {e}") from e


def _validate_list_type(param_name: str, args_type: tuple[Any, ...], data: list[Any]) -> list[Any]:
    """Validates specific list types (e.g., list[str], list[dict[str, str]])."""
    item_type = args_type[0]

    if item_type is str:
        if not all(isinstance(item, str) for item in data):
            raise TypeError(f"Expected a list of strings for '{param_name}'.")
        return data
    if item_type == dict[str, str]:
        if not all(
            isinstance(item, dict)
            and all(isinstance(k, str) for k in item)
            and all(isinstance(v, str) for v in item.values())
            for item in data
        ):
            raise TypeError(f"Expected a list of dicts with string keys/values for '{param_name}'.")
        return data
    # Handle lists of Pydantic models
    if isinstance(item_type, type) and issubclass(item_type, pydantic.BaseModel):
        return [item_type.model_validate(item) for item in data]

    # Add more list types if needed
    raise TypeError(f"Unsupported list item type {args_type} for '{param_name}'.")


def _validate_pydantic_model(
    param_name: str, param_type: type[pydantic.BaseModel], value_str: str
) -> pydantic.BaseModel:
    """Validates a string as a Pydantic model."""
    data = _parse_json_value(param_name, value_str)
    if not isinstance(data, dict):
        raise TypeError(f"Expected a JSON object string for Pydantic model '{param_name}'.")
    return param_type.model_validate(data)


def _validate_list(param_name: str, param_type: Any, value_str: str) -> list[Any]:
    """Validates a string as a list based on its type annotation."""
    data = _parse_json_value(param_name, value_str)
    if not isinstance(data, list):
        raise TypeError(f"Expected a JSON list string for '{param_name}'.")
    args_type = get_args(param_type)
    return _validate_list_type(param_name, args_type, data)  # Reuse existing helper


def _validate_bool(param_name: str, value_str: str) -> bool:
    """Validates a string as a boolean."""
    val_lower = value_str.lower()
    if val_lower == "true":
        return True
    if val_lower == "false":
        return False
    raise ValueError(f"Expected 'true' or 'false' for boolean '{param_name}'.")


# --- Argument Parsing and Validation ---


def _validate_argument_type(param_name: str, param_type: Any, value_str: str) -> Any:
    """Parses and validates a string value based on the expected parameter type."""
    try:
        if isinstance(param_type, type) and issubclass(param_type, pydantic.BaseModel):
            return _validate_pydantic_model(param_name, param_type, value_str)
        if get_origin(param_type) is list:
            return _validate_list(param_name, param_type, value_str)
        if param_type is int:
            return int(value_str)
        if param_type is bool:
            return _validate_bool(param_name, value_str)
        if param_type is str:
            return value_str  # String is the default if no other type matches

        # Fallback for Any or unhandled types
        logger.warning(
            "Attempting to pass argument '%s' without specific validation (type: %s). Treating as string.",
            param_name,
            param_type,
        )
        return value_str

    except (ValueError, TypeError, pydantic.ValidationError) as e:
        # Re-raise with more context for Typer
        raise ValueError(f"Invalid value for argument '{param_name}'. Expected {param_type}. Error: {e}") from e


def _parse_individual_args(input_args_list: list[str], method_sig: Signature, method_name: str) -> dict[str, Any]:
    """Parses a list of 'key=value' strings and validates against the method signature."""
    parsed_kwargs: dict[str, Any] = {}
    provided_args: set[str] = set()

    for arg_str in input_args_list:
        if "=" not in arg_str:
            raise typer.BadParameter(f"Invalid argument format '{arg_str}'. Expected 'key=value'.", param_hint="-i")

        key, value_str = arg_str.split("=", 1)

        if key not in method_sig.parameters or key == "self":
            raise typer.BadParameter(f"Unknown argument '{key}' for method '{method_name}'.", param_hint="-i")

        param_details = method_sig.parameters[key]
        param_type = param_details.annotation

        try:
            validated_value = _validate_argument_type(key, param_type, value_str)
            parsed_kwargs[key] = validated_value
            provided_args.add(key)  # Track provided args
        except (pydantic.ValidationError, TypeError, ValueError) as e:
            logger.error("Validation error for argument '%s' with value '%s': %s", key, value_str, e)
            # Use the error message from _validate_argument_type which includes context
            raise typer.BadParameter(str(e), param_hint=f"-i {key}=...") from e

    # Check for missing required arguments
    for param_name, param_details in method_sig.parameters.items():
        if param_name == "self":
            continue
        if param_details.default is Parameter.empty and param_name not in provided_args:
            logger.error("Missing required argument '%s'.", param_name)
            raise typer.BadParameter(f"Missing required argument '{param_name}'.", param_hint=f"-i {param_name}=...")

    return parsed_kwargs


def _print_result(result: Any) -> None:
    """Prints the command result in an appropriate format."""
    if isinstance(result, pydantic.BaseModel):
        # Use model_dump_json for proper serialization
        print(result.model_dump_json(indent=2))
    elif isinstance(result, list) and result and isinstance(result[0], pydantic.BaseModel):
        # Dump list of pydantic models
        print(json.dumps([item.model_dump(mode="json") for item in result], indent=2))
    elif result is None:
        print("Operation completed successfully (No content returned).")
    elif isinstance(result, bool):
        # Use indent=2 for consistency
        print(json.dumps({"success": result}, indent=2))
    else:
        # Default JSON dump for other types
        try:
            # Use default=str for types json doesn't handle natively
            print(json.dumps(result, indent=2, default=str))
        except TypeError:
            # If default=str still fails, print the error message and the object representation
            logger.warning("Result could not be serialized to standard JSON, even with default=str.")
            print(f"Command executed, but result could not be serialized to standard JSON: {result!r}")


# --- Helper Functions for Command Execution ---


async def _execute_api_call(
    method_name: str,
    method_sig: Signature,
    input_args: list[str] | None,
) -> None:
    """Handles argument parsing, client interaction, and result printing for a command."""
    client: EngineClient | None = cli_state.get("client")
    if not client:
        logger.error("Client not initialized. Exiting.")
        # Echo the message separately and raise Exit with only the code.
        typer.echo("Client not initialized.", err=True)
        raise typer.Exit(code=1)

    target_method = getattr(client, method_name)
    kwargs = {}

    try:
        # Parse and validate arguments
        if input_args:
            kwargs = _parse_individual_args(input_args, method_sig, method_name)
        else:
            # Check if the method requires arguments even if -i wasn't provided
            required_params = {
                p_name
                for p_name, p_details in method_sig.parameters.items()
                if p_name != "self" and p_details.default is Parameter.empty
            }
            if required_params:
                logger.error("Missing required arguments for %s: %s", method_name, required_params)
                raise typer.BadParameter(
                    f"Command '{method_name}' requires arguments, but none were provided via -i/--input. "
                    f"Required: {', '.join(required_params)}"
                )
            logger.info("No input arguments provided for %s, proceeding as it requires no arguments.", method_name)

        # Call the actual client method
        logger.info("Calling %s with validated args: %s", method_name, kwargs)
        result = await target_method(**kwargs)

        # Print the result
        _print_result(result)

    except ClientResponseError as e:
        logger.error("API call failed: Status=%s, Message=%s, URL=%s", e.status, e.message, e.request_info.url)
        error_body = "Could not retrieve error body."
        try:
            if client and client.session and not client.session.closed:
                error_body = e.message  # aiohttp message often contains body snippet
                logger.error("API Error Body Snippet: %s", error_body)
            else:
                logger.warning("Client session closed or unavailable, cannot read error body.")
        except Exception as read_err:
            logger.error("Failed to read error body: %s", read_err)

        typer.echo(
            f"Error: API call failed with status {e.status}.\nMessage: {e.message}\nBody Snippet: {error_body}",
            err=True,
        )
        raise typer.Exit(code=1) from e
    except typer.BadParameter:
        raise  # Re-raise for Typer to handle
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception("An unexpected error occurred during command execution.")
        typer.echo(f"An unexpected error occurred: {e}", err=True)
        # The message is echoed above. typer.Exit only takes the code.
        raise typer.Exit(code=1) from e
    finally:
        # Close session - consider if this is the right place long-term
        if client and client.session and not client.session.closed:
            logger.info("Closing client session after command %s.", method_name)
            await client.session.close()


def _create_sync_command_wrapper(
    method_name: str,
    method_sig: Signature,
    method_doc: str,
) -> Callable[[list[str] | None], None]:
    """Creates the synchronous Typer command wrapper."""

    def sync_command_wrapper(
        input_args: Annotated[
            list[str] | None,
            typer.Option(
                "--input",
                "-i",
                help=f"Argument for {method_name} in 'key=value' format. Repeat for multiple arguments. "
                f"Required if the command takes arguments. "
                f"Use JSON for complex types (objects, lists). Example: -i name=value -i data='{{ \"a\": 1 }}'",
            ),
        ] = None,
    ) -> None:
        """Synchronous wrapper to run the async command logic."""
        try:
            asyncio.run(_execute_api_call(method_name, method_sig, input_args))
        except (typer.Exit, typer.BadParameter):
            raise  # Let Typer handle its own exceptions
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception("An unexpected error occurred during command execution (sync wrapper).")
            typer.echo(f"An unexpected error occurred: {e}", err=True)
            # The message is echoed above. typer.Exit only takes the code.
            raise typer.Exit(code=1) from e

    sync_command_wrapper.__name__ = method_name.replace("_", "-")
    sync_command_wrapper.__doc__ = method_doc
    return sync_command_wrapper


# --- Typer App Setup ---
# Use a dictionary to store state, including the client instance
cli_state: dict[str, Any] = {}

cli = typer.Typer(  # Renamed app to cli
    name="enginepy",
    help="Enginepy CLI tool to interact with the Engine API.",
    add_completion=True,  # Enable shell completion
)


# Callback runs before any command, used for setup (config, client init)
@cli.callback(invoke_without_command=True)  # Renamed app to cli
def main_callback(
    ctx: typer.Context,
    config_path: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to the configuration file (YAML expected). Uses env vars or defaults if not provided.",
        exists=True,  # Typer checks if the file exists
        dir_okay=False,
        readable=True,
    ),
) -> None:
    """Main callback to initialize configuration and client."""
    if ctx.invoked_subcommand is None:
        # Show help if no command is given
        typer.echo(ctx.get_help())
        raise typer.Exit()

    # Load configuration
    try:
        # Use the actual config loader
        conf = config(path=config_path)

        # Basic logging setup based on config
        # Note: ant31box config handles logging setup internally based on its structure
        # We might not need explicit basicConfig here if using ant31box's logging setup.
        # Assuming ant31box config handles logging setup. If not, uncomment and adjust:
        # log_level = getattr(logging, conf.logging.level.upper(), logging.INFO)
        # logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        logger.info("Configuration loaded. Logging level: %s", conf.logging.level.upper())  # Access via property

        # Ensure engine config is present
        if not conf.engine or not conf.engine.endpoint or not conf.engine.token:
            msg = "Engine endpoint and token must be configured."
            logger.error(msg)
            typer.echo(msg, err=True)  # Echo the error message
            raise typer.Exit(code=1)  # Raise with code only

        # Initialize client and store in state
        # Note: Client session is created on first use by BaseClient
        client = EngineClient(config=conf.engine)
        cli_state["client"] = client
        logger.info("EngineClient initialized for endpoint: %s", conf.engine.endpoint)

    except Exception as e:  # pylint: disable=broad-exception-caught
        msg = f"Failed to initialize configuration or client: {e}"
        logger.exception(msg)
        typer.echo(msg, err=True)  # Echo the error message
        raise typer.Exit(code=1) from e  # Raise with code only


# --- Dynamic Command Creation ---
def create_cli_commands() -> None:
    """Inspects EngineClient and creates Click commands dynamically."""
    client_prototype = EngineClient  # Use the class for inspection
    # Explicitly exclude methods not intended for direct CLI invocation
    exclude_methods = {"__init__", "set_token", "headers", "_url", "log_request", "close"}

    for name, method in inspect.getmembers(client_prototype):
        # Filter for public async methods intended as API calls
        if inspect.iscoroutinefunction(method) and not name.startswith("_") and name not in exclude_methods:
            create_command_for_method(name, method)


class OutputFormat(StrEnum):
    TABLE = "table"
    JSON = "json"
    YAML = "yaml"


def _get_api_endpoints() -> list[ApiEndpoint]:
    """Inspects the EngineClient and returns a list of discovered API endpoints."""
    endpoints = []
    exclude_methods = {
        "__init__",
        "set_token",
        "headers",
        "_url",
        "log_request",
        "close",
        "action_triggers",  # Exclude wrappers
    }

    for name, _ in inspect.getmembers(EngineClient):
        if name in API_ENDPOINT_METADATA and name not in exclude_methods and not name.startswith("_"):
            meta = API_ENDPOINT_METADATA[name]
            endpoints.append(
                ApiEndpoint(
                    command=name.replace("_", "-"),
                    method_name=name,
                    path=meta["path"],
                    http_method=meta["method"],
                    token_preferences=meta["tokens"],
                )
            )
    return sorted(endpoints, key=lambda x: x.command)


@cli.command(name="list-endpoints", help="List all available API commands and their details.")
def list_endpoints(
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            "-o",
            help="The output format for the endpoint list.",
            case_sensitive=False,
        ),
    ] = OutputFormat.TABLE,
) -> None:
    """Lists all dynamically created API commands."""
    endpoints = _get_api_endpoints()
    if output == OutputFormat.JSON:
        print(json.dumps([ep.model_dump() for ep in endpoints], indent=2))
    elif output == OutputFormat.YAML:
        print(yaml.dump([ep.model_dump() for ep in endpoints], sort_keys=False))
    else:  # Default to table
        console = Console()
        table = Table(title="Available API Endpoints")
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("HTTP Method", style="yellow")
        table.add_column("API Path", style="blue")
        table.add_column("Client Method", style="magenta")
        table.add_column("Token Preference (Priority)", style="green")

        for endpoint in endpoints:
            token_str = ", ".join(t.value for t in endpoint.token_preferences) if endpoint.token_preferences else "default"
            table.add_row(
                endpoint.command,
                endpoint.http_method,
                endpoint.path,
                endpoint.method_name,
                token_str,
            )

        console.print(table)


def create_command_for_method(method_name: str, method_obj: Callable[..., Any]) -> None:
    """Creates and registers a single Typer command for a given EngineClient method."""
    # Check if the method is in our exposed endpoints list
    if method_name not in API_ENDPOINT_METADATA:
        return

    method_sig = inspect.signature(method_obj)
    method_doc = inspect.getdoc(method_obj) or f"Calls the {method_name} method."
    command_name = method_name.replace("_", "-")

    # Create the synchronous wrapper which calls the async execution logic
    sync_wrapper = _create_sync_command_wrapper(method_name, method_sig, method_doc)

    # Register the command with Typer
    cli.command(name=command_name, help=method_doc)(sync_wrapper)  # Renamed app to cli


# --- Initialization ---
# Create commands when the module is loaded
cli.add_typer(default_config_app)
create_cli_commands()


if __name__ == "__main__":
    cli()  # Renamed app to cli
