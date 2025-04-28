import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agents import Agent, RunContextWrapper, RunResult, TResponseInputItem

from enginepy.agents.case_summary.models import ConnyRequestSummary, ConnyRequestSummaryCtx, SummaryResponse

# Import classes/models to test
from enginepy.agents.case_summary.summary_agent import SummaryAgent
from enginepy.models import AgentRunCost

# --- Test Data ---
REQ_ID = 987
DATE_STR_NOW = datetime.datetime.now(datetime.UTC).isoformat()
PREVIOUS_SUMMARY = SummaryResponse(
    summary="Old summary", timeline="Old timeline", last_document_id="doc-old",
    last_document_date=DATE_STR_NOW,
    summary_changes=["old_change1", "old_change2"],
    timeline_changes=["old_changeA", "old_changeB"],
)
CASE_DATA_STR = '{"docs": [{"metadata": {"id": "doc-new", "date": "'+DATE_STR_NOW+'"}, "summary": "New data"}]}'

@pytest.fixture
def mock_model_provider(mocker) -> MagicMock:
    """Mocks the model provider."""
    mock_provider = MagicMock()
    mock_provider.get_model.return_value = "mock-model-name"  # Or a mock model object if needed
    mock_provider.model_settings = {"temperature": 0.5}
    return mock_provider

@pytest.fixture
def summary_agent_instance(mock_model_provider) -> SummaryAgent:
    """Provides a SummaryAgent instance with mocked provider."""
    # Temporarily patch the base class's __init__ if model_provider isn't directly passed
    with patch('antgent.agents.base.BaseAgent.__init__', return_value=None):
         agent = SummaryAgent()
         agent.model_provider = mock_model_provider  # Manually assign mock
         return agent

@pytest.fixture
def sample_ctx() -> ConnyRequestSummaryCtx:
    """Provides a basic ConnyRequestSummaryCtx."""
    req = ConnyRequestSummary(request_id=REQ_ID)
    return ConnyRequestSummaryCtx.from_summary(req)

@pytest.fixture
def sample_ctx_with_previous() -> ConnyRequestSummaryCtx:
    """Provides a ConnyRequestSummaryCtx with previous data."""
    req = ConnyRequestSummary(request_id=REQ_ID, previous=PREVIOUS_SUMMARY)
    return ConnyRequestSummaryCtx.from_summary(req)

@pytest.fixture
def mock_get_collection_summary(mocker) -> AsyncMock:
    """Mocks the get_collection_summary function."""
    return mocker.patch('enginepy.agents.case_summary.summary_agent.get_collection_summary', new_callable=AsyncMock)

# --- Tests ---

def test_summary_agent_name_and_provider(summary_agent_instance):
    """Test agent name and default provider."""
    assert summary_agent_instance.name == "SummaryAgent"
    assert summary_agent_instance.default_provider == "gemini"

def test_summary_agent_agent_method(summary_agent_instance, mock_model_provider):
    """Test the agent() method configures the underlying Agent correctly."""
    agent_config = summary_agent_instance.agent()

    assert isinstance(agent_config, Agent)
    assert agent_config.name == summary_agent_instance.name
    assert agent_config.model == mock_model_provider.get_model.return_value
    assert agent_config.instructions == summary_agent_instance.machine_instruction_v2  # Check it defaults to v2
    assert agent_config.output_type == SummaryResponse
    assert agent_config.model_settings == mock_model_provider.model_settings
    mock_model_provider.get_model.assert_called_once()

@pytest.mark.asyncio
async def test_prep_input_shortcut_retrieved_all(
    summary_agent_instance, sample_ctx, mock_get_collection_summary
):
    """Test prep_input shortcut when get_collection_summary sets retrieved_all."""
    sample_ctx.retrieved_all = False  # Start as False
    async def side_effect(ctx):
        ctx.retrieved_all = True  # Simulate function setting this
        return ""  # Return empty string for simplicity
    mock_get_collection_summary.side_effect = side_effect

    prep_run = await summary_agent_instance.prep_input(llm_input="", ctx=sample_ctx)

    mock_get_collection_summary.assert_called_once_with(sample_ctx)
    assert prep_run.short_cut is True
    assert prep_run.input == ""
    assert prep_run.context == sample_ctx

@pytest.mark.asyncio
async def test_prep_input_shortcut_no_case_data(
    summary_agent_instance, sample_ctx, mock_get_collection_summary
):
    """Test prep_input shortcut when get_collection_summary returns no data."""
    sample_ctx.retrieved_all = False
    mock_get_collection_summary.return_value = ""  # Simulate no data returned

    prep_run = await summary_agent_instance.prep_input(llm_input="some input", ctx=sample_ctx)

    mock_get_collection_summary.assert_called_once_with(sample_ctx)
    assert prep_run.short_cut is True
    assert prep_run.input == ""
    assert prep_run.context == sample_ctx
    assert sample_ctx.retrieved_all is False  # Should not be changed in this case

@pytest.mark.asyncio
async def test_prep_input_normal_flow_str_input_no_previous(
    summary_agent_instance, sample_ctx, mock_get_collection_summary
):
    """Test prep_input normal flow with string input and no previous context."""
    sample_ctx.retrieved_all = False
    mock_get_collection_summary.return_value = CASE_DATA_STR  # Simulate data returned

    llm_input_str = "User query string"
    prep_run = await summary_agent_instance.prep_input(llm_input=llm_input_str, ctx=sample_ctx)

    mock_get_collection_summary.assert_called_once_with(sample_ctx)
    assert prep_run.short_cut is False
    assert prep_run.context == sample_ctx

    expected_input_items: list[TResponseInputItem] = [
        {"content": "Newest documents and emails:", "role": "user"},
        {"content": CASE_DATA_STR, "role": "user"},
        {"content": llm_input_str, "role": "user"},  # The llm_input string
    ]
    assert prep_run.input == expected_input_items

@pytest.mark.asyncio
async def test_prep_input_normal_flow_list_input_with_previous(
    summary_agent_instance, sample_ctx_with_previous, mock_get_collection_summary
):
    """Test prep_input normal flow with list input and previous context."""
    sample_ctx_with_previous.retrieved_all = False
    mock_get_collection_summary.return_value = CASE_DATA_STR  # Simulate data returned

    llm_input_list: list[TResponseInputItem] = [{"content": "Item 1", "role": "assistant"}]
    prep_run = await summary_agent_instance.prep_input(llm_input=llm_input_list, ctx=sample_ctx_with_previous)

    mock_get_collection_summary.assert_called_once_with(sample_ctx_with_previous)
    assert prep_run.short_cut is False
    assert prep_run.context == sample_ctx_with_previous

    expected_input_items: list[TResponseInputItem] = [
        {"content": "Newest documents and emails:", "role": "user"},
        {"content": CASE_DATA_STR, "role": "user"},
        *llm_input_list,  # The llm_input list items
        {"content": f"previous summary to use: {PREVIOUS_SUMMARY.summary}", "role": "user"},
        {"content": f"previous timeline to use: {PREVIOUS_SUMMARY.timeline}", "role": "user"},
    ]
    assert prep_run.input == expected_input_items

@pytest.mark.asyncio
async def test_prep_response_none(summary_agent_instance, sample_ctx):
    """Test prep_response when input response is None."""
    result = await summary_agent_instance.prep_response(response=None, ctx=sample_ctx)
    assert result is None

@pytest.mark.asyncio
async def test_prep_response_updates_output(summary_agent_instance, sample_ctx):
    """Test prep_response updates the final_output with context dates."""
    # Set some dates in the context
    sample_ctx.last_document_date = DATE_STR_NOW
    sample_ctx.last_document_id = "doc-final-ctx"

    # Create a mock RunResult with a SummaryResponse
    mock_output = SummaryResponse(
        summary="Generated Summary", 
        timeline="Generated Timeline", 
        summary_changes=[], 
        timeline_changes=[], 
        last_document_id="", 
        last_document_date=""
    )
    mock_run_result = MagicMock(spec=RunResult)
    mock_run_result.final_output = mock_output
    mock_run_result.cost = AgentRunCost()  # Add cost if needed by RunResult structure

    result = await summary_agent_instance.prep_response(response=mock_run_result, ctx=sample_ctx)

    assert result is not None
    assert result == mock_run_result  # Should return the same object
    # Check that the final_output object was modified
    assert result.final_output.last_document_date == sample_ctx.last_document_date
    assert result.final_output.last_document_id == sample_ctx.last_document_id
    assert isinstance(result.final_output.last_document_date, str)  # Ensure still string

@patch('datetime.datetime', wraps=datetime.datetime)  # Mock datetime to control now()
def test_machine_instruction_v2(mock_dt, summary_agent_instance, sample_ctx):
    """Test machine_instruction_v2 structure and content."""
    fixed_now = datetime.datetime(2024, 7, 26, 12, 0, 0, tzinfo=datetime.UTC)
    mock_dt.now.return_value = fixed_now
    expected_date_str = fixed_now.strftime("%Y-%m-%d")

    mock_run_context = MagicMock(spec=RunContextWrapper)
    mock_run_context.context = sample_ctx
    mock_agent_config = MagicMock(spec=Agent)

    instruction = summary_agent_instance.machine_instruction_v2(mock_run_context, mock_agent_config)

    assert isinstance(instruction, str)
    assert "SYSTEM:" in instruction
    assert "INSTRUCTION:" in instruction
    assert "Create an executive summary" in instruction
    assert "mermaid format" in instruction
    assert "Today's date:" in instruction
    # Check that the expected date appears in the instruction text
    assert expected_date_str in instruction

@patch('datetime.datetime', wraps=datetime.datetime)  # Mock datetime to control now()
def test_machine_instruction_v1(mock_dt, summary_agent_instance, sample_ctx):
    """Test machine_instruction_v1 structure and content."""
    fixed_now = datetime.datetime(2024, 7, 26, 12, 0, 0, tzinfo=datetime.UTC)
    mock_dt.now.return_value = fixed_now
    expected_date_str = fixed_now.strftime("%Y-%m-%d")

    mock_run_context = MagicMock(spec=RunContextWrapper)
    mock_run_context.context = sample_ctx
    mock_agent_config = MagicMock(spec=Agent)

    instruction = summary_agent_instance.machine_instruction_v1(mock_run_context, mock_agent_config)

    assert isinstance(instruction, str)
    assert "SYSTEM:" in instruction
    assert "INSTRUCTION:" in instruction
    assert f"Today's date is: {expected_date_str}" in instruction
    assert "Summarize the case status from the beginning" in instruction
    assert "mermaid format" in instruction
    assert "get_collection_summary_tool" in instruction
    assert "plan_steps_to_build_summary" in instruction
@pytest.mark.asyncio
async def test_prep_input_empty_string_input_no_previous(summary_agent_instance, sample_ctx, mock_get_collection_summary):
    """Test prep_input normal flow with empty string input and no previous context."""
    sample_ctx.retrieved_all = False
    mock_get_collection_summary.return_value = CASE_DATA_STR  # Simulate data returned

    llm_input_str = ""  # Empty string input
    prep_run = await summary_agent_instance.prep_input(llm_input=llm_input_str, ctx=sample_ctx)

    mock_get_collection_summary.assert_called_once_with(sample_ctx)
    assert prep_run.short_cut is False
    assert prep_run.context == sample_ctx

    expected_input_items = [
        {"content": "Newest documents and emails:", "role": "user"},
        {"content": CASE_DATA_STR, "role": "user"},
    ]
    assert prep_run.input == expected_input_items
