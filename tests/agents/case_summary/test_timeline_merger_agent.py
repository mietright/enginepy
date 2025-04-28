import json
from unittest.mock import MagicMock, patch

import pytest
from agents import Agent, RunContextWrapper, TResponseInputItem

from enginepy.agents.case_summary.functions import system_instruction  # For prompt check
from enginepy.agents.case_summary.models import (
    ConnyRequestSummary,
    ConnyRequestSummaryCtx,
    SummaryResponse,
    TimelineMergerResponse,
)

# Import classes/models to test
from enginepy.agents.case_summary.timeline_merger_agent import TimelineMergerAgent

# --- Test Data ---
REQ_ID = 666
SUMMARY_RESP_1 = SummaryResponse(summary="Summary part 1", timeline="Timeline 1",
                                 summary_changes=[], timeline_changes=[],
                                 last_document_id="doc-1", last_document_date="2024-01-15T10:30:00Z",
                                 )
SUMMARY_RESP_2 = SummaryResponse(summary="Summary part 2",
                                 timeline="Timeline 2",
                                 summary_changes=[], timeline_changes=[],
                                 last_document_id="doc-2", last_document_date="2024-01-15T11:30:00Z",
                                 )
INPUT_SUMMARIES = [SUMMARY_RESP_1, SUMMARY_RESP_2]

@pytest.fixture
def mock_model_provider(mocker) -> MagicMock:
    """Mocks the model provider."""
    mock_provider = MagicMock()
    mock_provider.get_model.return_value = "mock-timeline-model"
    mock_provider.model_settings = {"temperature": 0.2}
    return mock_provider

@pytest.fixture
def timeline_merger_agent_instance(mock_model_provider) -> TimelineMergerAgent:
    """Provides a TimelineMergerAgent instance with mocked provider."""
    with patch('antgent.agents.base.BaseAgent.__init__', return_value=None):
         agent = TimelineMergerAgent()
         agent.model_provider = mock_model_provider  # Manually assign mock
         return agent

@pytest.fixture
def sample_ctx() -> ConnyRequestSummaryCtx:
    """Provides a basic ConnyRequestSummaryCtx."""
    req = ConnyRequestSummary(request_id=REQ_ID)
    return ConnyRequestSummaryCtx.from_summary(req)

# --- Tests ---

def test_timeline_merger_agent_name_and_provider(timeline_merger_agent_instance):
    """Test agent name and default provider."""
    assert timeline_merger_agent_instance.name == "TimelineMergerAgent"
    assert timeline_merger_agent_instance.default_provider == "openai"

def test_timeline_merger_agent_agent_method(timeline_merger_agent_instance, mock_model_provider):
    """Test the agent() method configures the underlying Agent correctly."""
    agent_config = timeline_merger_agent_instance.agent()

    assert isinstance(agent_config, Agent)
    assert agent_config.name == timeline_merger_agent_instance.name
    assert agent_config.model == mock_model_provider.get_model.return_value
    assert agent_config.instructions == timeline_merger_agent_instance.machine_instruction_v1_ctx
    assert agent_config.output_type == TimelineMergerResponse  # Check correct output type
    assert agent_config.model_settings == mock_model_provider.model_settings
    mock_model_provider.get_model.assert_called_once()

@pytest.mark.asyncio
async def test_prep_input(timeline_merger_agent_instance, sample_ctx):
    """Test prep_input formats the input list correctly."""
    prep_run = await timeline_merger_agent_instance.prep_input(llm_input=INPUT_SUMMARIES, ctx=sample_ctx)

    assert prep_run.short_cut is False
    assert prep_run.context == sample_ctx

    # Expected JSON structure: list of strings, each being a JSON dump of one input summary including ONLY 'timeline'
    expected_inner_json_list = [
        SUMMARY_RESP_1.model_dump_json(indent=2, include={"timeline"}),
        SUMMARY_RESP_2.model_dump_json(indent=2, include={"timeline"}),
    ]
    expected_outer_json = json.dumps(expected_inner_json_list, indent=2)

    expected_input_items: list[TResponseInputItem] = [
        {"content": "Merge:\n", "role": "user"},
        {"content": expected_outer_json, "role": "user"},
    ]
    assert prep_run.input == expected_input_items

def test_machine_instruction_v1(timeline_merger_agent_instance, sample_ctx):
    """Test machine_instruction_v1 structure and content."""
    mock_run_context = MagicMock(spec=RunContextWrapper)
    mock_run_context.context = sample_ctx
    mock_agent_config = MagicMock(spec=Agent)

    instruction = timeline_merger_agent_instance.machine_instruction_v1_ctx(mock_run_context, mock_agent_config)

    assert isinstance(instruction, str)
    assert "SYSTEM:" in instruction
    assert "INSTRUCTION:" in instruction
    assert system_instruction() in instruction  # Check base system instruction included
    assert "Review multiple timelines" in instruction
    assert "mermaid timeline diagram format" in instruction
    assert "Output Format" in instruction
    assert "```json" in instruction
    assert '"timeline": "the merged timeline"' in instruction
    assert '"changes": "added timeline events"' in instruction  # Check example format hint
