# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=too-many-arguments
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientResponseError
from pydantic import Field
from pydantic_settings import SettingsConfigDict
from typer.testing import CliRunner

import enginepy.cli
from enginepy.cli import cli
from enginepy.config import Config, ConfigSchema, EngineConfigSchema, LogfireConfigSchema, LoggingCustomConfigSchema
from enginepy.engine_client import EngineClient
from enginepy.models import EngineRequest, EngineTrigger


# --- Fixtures ---
@pytest.fixture
def runner() -> CliRunner:
    """Provides a Typer CliRunner instance."""
    return CliRunner()


@pytest.fixture
def mock_config_instance() -> Config:
    """Provides a mocked Config instance with basic settings."""
    mock_conf_schema = ConfigSchema(
        name="test-enginepy",
        logfire=LogfireConfigSchema(token="logfire-token"),
        engine=EngineConfigSchema(endpoint="http://fake-engine.local", token="engine-token"),
        logging=LoggingCustomConfigSchema(level="INFO"),
        model_config=SettingsConfigDict(env_prefix="TEST_", case_sensitive=False, extra="allow"),
    )
    mock_config_obj = Config()
    mock_config_obj.conf = mock_conf_schema
    return mock_config_obj


@pytest.fixture
def mock_engine_client() -> MagicMock:
    """Provides a mocked EngineClient instance with async methods."""
    mock_client = MagicMock(spec=EngineClient)
    # Mock async methods needed for commands
    mock_client.health = AsyncMock(return_value=True)
    mock_client.get_case_data = AsyncMock(return_value={"case_id": 123, "status": "ok"})
    mock_client.update_doc = AsyncMock(return_value=True)
    mock_client.action_trigger = AsyncMock(
        return_value=EngineTrigger(trigger_id="t1", request_id=1, status={"result": "triggered"})
    )
    mock_client.create_request = AsyncMock(return_value={"request_id": 456, "status": "created"})
    mock_client.update_request = AsyncMock(return_value={"status": "updated"})
    mock_client.update_insights = AsyncMock(return_value={"message": "insights updated"})
    mock_client.update_doc_suggestions = AsyncMock(return_value={"message": "suggestions updated"})
    # Mock the session close method
    mock_client.session = MagicMock()
    mock_client.session.close = AsyncMock()
    return mock_client


@pytest.fixture(autouse=True)
def patch_dependencies(mock_config_instance: Config, mock_engine_client: MagicMock):
    """Patches config loading and client instantiation for all tests."""
    with patch("enginepy.cli.config", return_value=mock_config_instance) as mock_load_config, patch(
        "enginepy.cli.EngineClient", return_value=mock_engine_client
    ) as mock_client_class, patch("enginepy.cli._execute_api_call") as mock_execute_api_call:
        # Store mocks for potential direct assertion if needed, though patching _execute_api_call is often enough
        enginepy.cli.cli_state["mock_load_config"] = mock_load_config
        enginepy.cli.cli_state["mock_client_class"] = mock_client_class
        enginepy.cli.cli_state["mock_execute_api_call"] = mock_execute_api_call
        yield mock_load_config, mock_client_class, mock_execute_api_call


# --- Test Cases ---


def test_cli_no_command_shows_help(runner: CliRunner):
    """Verify that running the CLI with no command shows help."""
    result = runner.invoke(cli)
    assert result.exit_code == 0  # Typer exits 0 when showing help via callback
    assert "Usage: enginepy [OPTIONS] COMMAND [ARGS]..." in result.stdout
    assert "Enginepy CLI tool to interact with the Engine API." in result.stdout


def test_cli_main_callback_success(runner: CliRunner, mock_config_instance: Config, mock_engine_client: MagicMock):
    """Test successful initialization via the main callback."""
    # We need to invoke a command for the callback to fully execute client init
    # Patch _execute_api_call to prevent the actual command logic from running
    with patch("enginepy.cli._execute_api_call", new_callable=AsyncMock) as mock_execute:
        result = runner.invoke(cli, ["health"])

    assert result.exit_code == 0
    # Check that config was loaded (mocked)
    assert enginepy.cli.cli_state["mock_load_config"].called
    # Check that client was initialized (mocked)
    assert enginepy.cli.cli_state["mock_client_class"].call_count == 1
    assert enginepy.cli.cli_state["mock_client_class"].call_args[1]["endpoint"] == mock_config_instance.engine.endpoint
    assert enginepy.cli.cli_state["mock_client_class"].call_args[1]["token"] == mock_config_instance.engine.token
    # Check that the client is stored in state
    assert enginepy.cli.cli_state.get("client") is mock_engine_client
    # Check that the command's execute function was called
    assert mock_execute.called


def test_cli_main_callback_config_load_failure(runner: CliRunner):
    """Test CLI exit when config loading fails."""
    with patch("enginepy.cli.config", side_effect=FileNotFoundError("Config file not found")) as mock_load_config:
        result = runner.invoke(cli, ["health"])

    assert result.exit_code == 1
    assert "Failed to initialize configuration or client" in result.stdout
    assert "Config file not found" in result.stdout
    assert mock_load_config.called


def test_cli_main_callback_missing_engine_config(runner: CliRunner, mock_config_instance: Config):
    """Test CLI exit when engine config is incomplete."""
    mock_config_instance.conf.engine = None  # Simulate missing engine config section
    with patch("enginepy.cli.config", return_value=mock_config_instance):
        result = runner.invoke(cli, ["health"])

    assert result.exit_code == 1
    assert "Engine endpoint and token must be configured." in result.stdout


# --- Test Command Invocation (using patched _execute_api_call) ---
# These tests verify that Typer correctly parses the command and options,
# and calls the underlying (mocked) execution logic.


def test_cli_health_command(runner: CliRunner):
    """Test invoking the 'health' command."""
    result = runner.invoke(cli, ["health"])
    assert result.exit_code == 0
    # Check that _execute_api_call was called with the correct method name
    mock_execute: AsyncMock = enginepy.cli.cli_state["mock_execute_api_call"]
    mock_execute.assert_awaited_once()
    assert mock_execute.call_args[0][0] == "health"  # method_name
    assert mock_execute.call_args[0][2] is None  # input_args


def test_cli_get_case_data_command_with_args(runner: CliRunner):
    """Test invoking 'get-case-data' with input arguments."""
    result = runner.invoke(cli, ["get-case-data", "-i", "request_id=123"])
    assert result.exit_code == 0
    mock_execute: AsyncMock = enginepy.cli.cli_state["mock_execute_api_call"]
    mock_execute.assert_awaited_once()
    assert mock_execute.call_args[0][0] == "get_case_data"
    assert mock_execute.call_args[0][2] == ["request_id=123"]  # input_args


def test_cli_command_with_json_arg(runner: CliRunner):
    """Test invoking a command with a JSON string argument."""
    json_payload = '{"product": "test", "funnel": "test", "fields": [{"field": "f1", "answer": "a1"}]}'
    result = runner.invoke(cli, ["create-request", "-i", f"enginereq={json_payload}"])
    assert result.exit_code == 0
    mock_execute: AsyncMock = enginepy.cli.cli_state["mock_execute_api_call"]
    mock_execute.assert_awaited_once()
    assert mock_execute.call_args[0][0] == "create_request"
    assert mock_execute.call_args[0][2] == [f"enginereq={json_payload}"]


def test_cli_command_with_multiple_args(runner: CliRunner):
    """Test invoking a command with multiple -i arguments."""
    result = runner.invoke(cli, ["update-doc", "-i", "doc_id=456", "-i", 'ocr_pages=["page1", "page2"]'])
    assert result.exit_code == 0
    mock_execute: AsyncMock = enginepy.cli.cli_state["mock_execute_api_call"]
    mock_execute.assert_awaited_once()
    assert mock_execute.call_args[0][0] == "update_doc"
    assert mock_execute.call_args[0][2] == ["doc_id=456", 'ocr_pages=["page1", "page2"]']


def test_cli_command_missing_required_arg_option(runner: CliRunner):
    """Test invoking a command that requires args without the -i option."""
    # We need to let _execute_api_call run partially to hit the argument check
    original_execute = enginepy.cli._execute_api_call
    with patch("enginepy.cli._execute_api_call", side_effect=original_execute) as mock_execute_partially:
        # Mock the client method itself to prevent actual call
        mock_client = enginepy.cli.cli_state["client"]
        mock_client.get_case_data = AsyncMock()

        result = runner.invoke(cli, ["get-case-data"]) # No -i provided

    assert result.exit_code == 1 # Should fail with BadParameter
    assert "Missing required arguments for get_case_data" in result.stdout
    assert "Required: request_id" in result.stdout
    assert mock_execute_partially.called # Ensure the patched function was entered


# --- Test _execute_api_call directly (more granular) ---
# These tests focus on the logic within _execute_api_call itself.

@pytest.mark.asyncio
async def test_execute_api_call_success(mock_engine_client: MagicMock, capsys):
    """Test successful execution within _execute_api_call."""
    method_name = "get_case_data"
    method_sig = inspect.signature(mock_engine_client.get_case_data)
    input_args = ["request_id=123"]
    expected_result = {"case_id": 123, "status": "ok"}
    mock_engine_client.get_case_data.return_value = expected_result
    enginepy.cli.cli_state["client"] = mock_engine_client # Ensure client is set

    await enginepy.cli._execute_api_call(method_name, method_sig, input_args)

    mock_engine_client.get_case_data.assert_awaited_once_with(request_id=123)
    captured = capsys.readouterr()
    assert json.dumps(expected_result, indent=2) in captured.out


@pytest.mark.asyncio
async def test_execute_api_call_pydantic_arg_success(mock_engine_client: MagicMock, capsys):
    """Test _execute_api_call with a Pydantic model argument."""
    method_name = "create_request"
    method_sig = inspect.signature(mock_engine_client.create_request)
    json_payload = '{"product": "pydantic_test", "funnel": "test", "fields": [{"field": "f1", "answer": "a1"}]}'
    input_args = [f"enginereq={json_payload}"]
    expected_pydantic_arg = EngineRequest.model_validate(json.loads(json_payload))
    expected_result = {"request_id": 789, "status": "created"}
    mock_engine_client.create_request.return_value = expected_result
    enginepy.cli.cli_state["client"] = mock_engine_client

    await enginepy.cli._execute_api_call(method_name, method_sig, input_args)

    # Pydantic models compared by value
    mock_engine_client.create_request.assert_awaited_once_with(enginereq=expected_pydantic_arg)
    captured = capsys.readouterr()
    assert json.dumps(expected_result, indent=2) in captured.out


@pytest.mark.asyncio
async def test_execute_api_call_list_arg_success(mock_engine_client: MagicMock, capsys):
    """Test _execute_api_call with a list argument."""
    method_name = "update_doc"
    method_sig = inspect.signature(mock_engine_client.update_doc)
    input_args = ["doc_id=999", 'ocr_pages=["p1", "p2"]', "searchable_pdf=http://example.com"]
    expected_result = True
    mock_engine_client.update_doc.return_value = expected_result
    enginepy.cli.cli_state["client"] = mock_engine_client

    await enginepy.cli._execute_api_call(method_name, method_sig, input_args)

    mock_engine_client.update_doc.assert_awaited_once_with(
        doc_id=999, ocr_pages=["p1", "p2"], searchable_pdf="http://example.com"
    )
    captured = capsys.readouterr()
    assert json.dumps({"success": True}) in captured.out


@pytest.mark.asyncio
async def test_execute_api_call_api_error(mock_engine_client: MagicMock, capsys):
    """Test _execute_api_call handling ClientResponseError."""
    method_name = "get_case_data"
    method_sig = inspect.signature(mock_engine_client.get_case_data)
    input_args = ["request_id=404"]

    # Mock the error response
    mock_response = MagicMock()
    mock_response.status = 404
    mock_response.reason = "Not Found"
    mock_request_info = MagicMock()
    mock_request_info.url = "http://fake-engine.local/api/case_data?request_id=404"
    error = ClientResponseError(
        request_info=mock_request_info,
        history=(),
        status=404,
        message="Case not found",
        headers={},
    )
    mock_engine_client.get_case_data.side_effect = error
    enginepy.cli.cli_state["client"] = mock_engine_client

    with pytest.raises(typer.Exit) as exc_info:
        await enginepy.cli._execute_api_call(method_name, method_sig, input_args)

    assert exc_info.value.exit_code == 1
    captured = capsys.readouterr()
    assert "Error: API call failed with status 404" in captured.err
    assert "Message: Case not found" in captured.err
    # Check if the mock was called
    mock_engine_client.get_case_data.assert_awaited_once_with(request_id=404)


@pytest.mark.asyncio
async def test_execute_api_call_validation_error(mock_engine_client: MagicMock, capsys):
    """Test _execute_api_call handling argument validation errors."""
    method_name = "get_case_data"
    method_sig = inspect.signature(mock_engine_client.get_case_data)
    input_args = ["request_id=not_an_int"] # Invalid integer
    enginepy.cli.cli_state["client"] = mock_engine_client

    with pytest.raises(typer.BadParameter) as exc_info:
        await enginepy.cli._execute_api_call(method_name, method_sig, input_args)

    assert "Invalid value for argument 'request_id'" in str(exc_info.value)
    assert "invalid literal for int()" in str(exc_info.value)
    # Ensure the API call was *not* made
    mock_engine_client.get_case_data.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_api_call_missing_required_arg(mock_engine_client: MagicMock, capsys):
    """Test _execute_api_call handling missing required arguments."""
    method_name = "get_case_data"
    method_sig = inspect.signature(mock_engine_client.get_case_data)
    input_args = [] # Missing request_id
    enginepy.cli.cli_state["client"] = mock_engine_client

    with pytest.raises(typer.BadParameter) as exc_info:
        await enginepy.cli._execute_api_call(method_name, method_sig, input_args)

    assert "Missing required argument 'request_id'" in str(exc_info.value)
    mock_engine_client.get_case_data.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_api_call_unexpected_error(mock_engine_client: MagicMock, capsys):
    """Test _execute_api_call handling unexpected errors during API call."""
    method_name = "health"
    method_sig = inspect.signature(mock_engine_client.health)
    input_args = None
    mock_engine_client.health.side_effect = RuntimeError("Something broke")
    enginepy.cli.cli_state["client"] = mock_engine_client

    with pytest.raises(typer.Exit) as exc_info:
        await enginepy.cli._execute_api_call(method_name, method_sig, input_args)

    assert exc_info.value.exit_code == 1
    captured = capsys.readouterr()
    assert "An unexpected error occurred: Something broke" in captured.err
    mock_engine_client.health.assert_awaited_once()


# --- Test Argument Parsing Helpers ---
import inspect
from enginepy.models import EngineField, EngineTypeEnum

def test_parse_individual_args_success():
    """Test _parse_individual_args with various valid types."""
    class TestModel(pydantic.BaseModel):
        name: str
        value: int

    def sample_method(self, req_id: int, name: str, data: TestModel, items: list[str], flag: bool = False): pass
    sig = inspect.signature(sample_method)
    method_name = "sample_method"
    args_list = [
        "req_id=123",
        "name=test_name",
        'data={"name": "model_name", "value": 42}',
        'items=["a", "b"]',
        "flag=true"
    ]

    parsed = enginepy.cli._parse_individual_args(args_list, sig, method_name)

    assert parsed == {
        "req_id": 123,
        "name": "test_name",
        "data": TestModel(name="model_name", value=42),
        "items": ["a", "b"],
        "flag": True
    }

def test_parse_individual_args_missing_required():
    """Test _parse_individual_args raises error for missing required arg."""
    def sample_method(self, req_id: int, name: str): pass
    sig = inspect.signature(sample_method)
    method_name = "sample_method"
    args_list = ["req_id=123"] # Missing 'name'

    with pytest.raises(typer.BadParameter) as exc_info:
        enginepy.cli._parse_individual_args(args_list, sig, method_name)
    assert "Missing required argument 'name'" in str(exc_info.value)

def test_parse_individual_args_unknown_arg():
    """Test _parse_individual_args raises error for unknown arg."""
    def sample_method(self, req_id: int): pass
    sig = inspect.signature(sample_method)
    method_name = "sample_method"
    args_list = ["req_id=123", "unknown_arg=abc"]

    with pytest.raises(typer.BadParameter) as exc_info:
        enginepy.cli._parse_individual_args(args_list, sig, method_name)
    assert "Unknown argument 'unknown_arg'" in str(exc_info.value)

def test_parse_individual_args_invalid_format():
    """Test _parse_individual_args raises error for invalid format."""
    def sample_method(self, req_id: int): pass
    sig = inspect.signature(sample_method)
    method_name = "sample_method"
    args_list = ["req_id123"] # Missing '='

    with pytest.raises(typer.BadParameter) as exc_info:
        enginepy.cli._parse_individual_args(args_list, sig, method_name)
    assert "Invalid argument format 'req_id123'" in str(exc_info.value)

def test_parse_individual_args_validation_error():
    """Test _parse_individual_args raises error for type validation failure."""
    def sample_method(self, req_id: int): pass
    sig = inspect.signature(sample_method)
    method_name = "sample_method"
    args_list = ["req_id=abc"] # Not an int

    with pytest.raises(typer.BadParameter) as exc_info:
        enginepy.cli._parse_individual_args(args_list, sig, method_name)
    assert "Invalid value for argument 'req_id'" in str(exc_info.value)
    assert "invalid literal for int()" in str(exc_info.value)


# --- Test _print_result ---

def test_print_result_pydantic_model(capsys):
    """Test printing a single Pydantic model."""
    model = EngineRequest(product="p", funnel="f", fields=[EngineField(field="f1", answer="a1")])
    enginepy.cli._print_result(model)
    captured = capsys.readouterr()
    expected_json = model.model_dump_json(indent=2)
    assert captured.out.strip() == expected_json


def test_print_result_list_of_pydantic_models(capsys):
    """Test printing a list of Pydantic models."""
    models = [
        EngineTrigger(trigger_id="t1", request_id=1, status={"s": 1}),
        EngineTrigger(trigger_id="t2", request_id=1, status={"s": 2}),
    ]
    enginepy.cli._print_result(models)
    captured = capsys.readouterr()
    expected_json = json.dumps([m.model_dump(mode="json") for m in models], indent=2)
    assert captured.out.strip() == expected_json


def test_print_result_bool_true(capsys):
    """Test printing a boolean True result."""
    enginepy.cli._print_result(True)
    captured = capsys.readouterr()
    assert captured.out.strip() == '{\n  "success": true\n}'


def test_print_result_bool_false(capsys):
    """Test printing a boolean False result."""
    enginepy.cli._print_result(False)
    captured = capsys.readouterr()
    assert captured.out.strip() == '{\n  "success": false\n}'


def test_print_result_dict(capsys):
    """Test printing a dictionary result."""
    data = {"key": "value", "number": 123}
    enginepy.cli._print_result(data)
    captured = capsys.readouterr()
    expected_json = json.dumps(data, indent=2)
    assert captured.out.strip() == expected_json


def test_print_result_none(capsys):
    """Test printing a None result."""
    enginepy.cli._print_result(None)
    captured = capsys.readouterr()
    assert captured.out.strip() == "Operation completed successfully (No content returned)."


def test_print_result_unserializable(capsys):
    """Test printing an unserializable object."""
    class Unserializable:
        pass
    obj = Unserializable()
    enginepy.cli._print_result(obj)
    captured = capsys.readouterr()
    assert "Command executed, but result could not be serialized to standard JSON" in captured.out
    assert str(obj) in captured.out # Check if the object's string representation is included
