from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

# Import necessary models
from enginepy.agents.case_summary.models import (
    ConnyRequestSummary,
    ConnyRequestSummaryCtx,
    SummaryMergerResponse,
    SummaryResponse,
    TimelineMergerResponse,
)
from enginepy.models import AgentRunCost  # Assuming AgentRunCost might be part of RunResult if needed

# Import the class to test
from enginepy.workflows.update_summary import UpdateSummaryWorkflow

# --- Test Data ---

SAMPLE_REQ_DICT = {
    "query": "Summarize recent events",
    "request_id": 456,
    "max_docs": 50,
}
SAMPLE_REQ = ConnyRequestSummary(**SAMPLE_REQ_DICT)
# Define datetime objects for reuse
DATE_1 = datetime(2023, 1, 10, tzinfo=UTC)
DATE_2 = datetime(2023, 1, 20, tzinfo=UTC)

# Sample SummaryResponse objects for mocking agent returns
SUMMARY_RESP_1 = SummaryResponse(
    summary="Initial summary part 1.",
    timeline="Event A happened.",
    last_document_id="doc-10",
    last_document_date=DATE_1.isoformat(),
    summary_changes=[],
    timeline_changes=[],
)
SUMMARY_RESP_2 = SummaryResponse(
    summary="Update summary part 2.",
    timeline="Event B followed.",
    last_document_id="doc-20",
    last_document_date=DATE_2.isoformat(),
    summary_changes=[],
    timeline_changes=[],
)
MERGED_SUMMARY_RESP = SummaryResponse(
    summary="Merged summary.",
    timeline="Merged timeline.",
    summary_changes=["Change 1"],
    timeline_changes=["Change A"],
    last_document_id="doc-20",  # From last iterative summary
    last_document_date=DATE_2.isoformat(),  # From last iterative summary
)
MERGED_TIMELINE_RESP = TimelineMergerResponse( # Mock response from TimelineMergerAgent
    timeline="Merged timeline.",
    changes=["Change A"],
)
MERGED_SUMMARY_ONLY_RESP = SummaryMergerResponse( # Mock response from SummaryMergerAgent
    summary="Merged summary.",
    changes=["Change 1"],
    # Assuming timeline is not generated in this case
)

# Mock RunResult structure (adjust if your actual RunResult is different)
class MockRunResult:
    def __init__(self, final_output, cost=None):
        self.final_output = final_output
        self.cost = cost or AgentRunCost()

    def __eq__(self, other):
        # When compared to a SummaryResponse, compare using the final_output value.
        # Also handle comparison with another MockRunResult if needed for other tests
        if isinstance(other, MockRunResult):
            return self.final_output == other.final_output
        return self.final_output == other

# --- Fixtures ---

@pytest.fixture
def sample_ctx() -> ConnyRequestSummaryCtx:
    """Provides a default ConnyRequestSummaryCtx instance."""
    return ConnyRequestSummaryCtx.from_summary(SAMPLE_REQ)

@pytest.fixture
def mock_summary_agent(mocker) -> AsyncMock:
    """Mocks the SummaryAgent instance and its run method."""
    mock = AsyncMock()
    mock.run = AsyncMock()  # Ensure run is async
    mocker.patch('enginepy.workflows.update_summary.SummaryAgent', return_value=mock)
    return mock

@pytest.fixture
def mock_summary_merger_agent(mocker) -> AsyncMock:
    """Mocks the SummaryMergerAgent instance and its run method."""
    mock = AsyncMock()
    mock.run_openai = AsyncMock() # Mock the correct method
    mocker.patch('enginepy.workflows.update_summary.SummaryMergerAgent', return_value=mock)
    return mock

@pytest.fixture
def mock_timeline_merger_agent(mocker) -> AsyncMock:
    """Mocks the TimelineMergerAgent instance and its run method."""
    mock = AsyncMock()
    mock.run_openai = AsyncMock() # Mock the correct method
    mocker.patch('enginepy.workflows.update_summary.TimelineMergerAgent', return_value=mock)
    return mock

@pytest.fixture(autouse=True)
def mock_tracing(mocker):
    """Mocks the trace and custom_span context managers."""
    # Patch trace and return the patch object to allow inspection
    trace_patcher = mocker.patch('enginepy.workflows.update_summary.trace', return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
    mocker.patch('enginepy.workflows.update_summary.custom_span', return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
    return trace_patcher # Return the patcher for 'trace'

@pytest.fixture
def mock_uuid(mocker):
    """Mocks uuid.uuid4().hex to return a fixed value."""
    mock_uuid_obj = MagicMock()
    mock_uuid_obj.hex = "fixeduuidhex1234"
    # Patch uuid.uuid4 and return the patch object itself
    patcher = mocker.patch('enginepy.workflows.update_summary.uuid.uuid4', return_value=mock_uuid_obj)
    return patcher

# --- Test Class ---

class TestUpdateSummaryWorkflow:

    def test_init_defaults(self):
        """Test workflow initialization with default max_iterations."""
        workflow = UpdateSummaryWorkflow()
        assert workflow.max_iterations == 10
        # Check if agents are instantiated (mocks will be used if fixtures are active)
        assert hasattr(workflow, 'summary_agent')
        assert hasattr(workflow, 'summary_merger_agent')
        assert hasattr(workflow, 'timeline_merger_agent')

    def test_init_custom_iterations(self):
        """Test workflow initialization with custom max_iterations."""
        workflow = UpdateSummaryWorkflow(max_iterations=5)
        assert workflow.max_iterations == 5

    @pytest.mark.asyncio
    async def test_update_summary_iterates_until_retrieved_all(
        self, sample_ctx, mock_summary_agent
    ):
        """Test update_summary stops when ctx.retrieved_all becomes True."""
        workflow = UpdateSummaryWorkflow(max_iterations=5)
        sample_ctx.retrieved_all = False  # Start condition

        # Define side effect for mock agent run
        async def side_effect(*args, **kwargs):
            context = kwargs.get('context') or args[1]  # Get the context passed to run
            call_count = mock_summary_agent.run.call_count
            if call_count == 1:
                # First call, return first summary, keep retrieved_all False
                # Simulate agent updating context with the DATETIME object
                context.last_document_date = DATE_1
                return MockRunResult(final_output=SUMMARY_RESP_1)
            elif call_count == 2:
                # Second call, return second summary, set retrieved_all True
                # Simulate agent updating context with the DATETIME object
                context.last_document_date = DATE_2
                context.retrieved_all = True  # Simulate finding all documents
                return MockRunResult(final_output=SUMMARY_RESP_2)
            else:
                # Should not be called more than twice
                pytest.fail("SummaryAgent.run called too many times")

        mock_summary_agent.run.side_effect = side_effect

        summaries = await workflow.update_summary(ctx=sample_ctx)

        assert len(summaries) == 2
        assert summaries[0] == SUMMARY_RESP_1
        assert summaries[1] == SUMMARY_RESP_2
        assert mock_summary_agent.run.call_count == 2
        # Check calls were made with the correct context (or verify context updates)
        mock_summary_agent.run.assert_has_calls([
            call(input="", context=sample_ctx),
            call(input="", context=sample_ctx),
        ])
        assert sample_ctx.retrieved_all is True  # Verify context was updated

    @pytest.mark.asyncio
    async def test_update_summary_stops_at_max_iterations(
        self, sample_ctx, mock_summary_agent
    ):
        """Test update_summary stops when max_iterations is reached."""
        max_iter = 3
        workflow = UpdateSummaryWorkflow(max_iterations=max_iter)
        sample_ctx.retrieved_all = False

        # Agent always returns a summary and never sets retrieved_all=True
        mock_summary_agent.run.return_value = MockRunResult(final_output=SUMMARY_RESP_1)

        summaries = await workflow.update_summary(ctx=sample_ctx)

        assert len(summaries) == max_iter + 1  # Iterations are 0-based, so max_iter=3 means 0, 1, 2, 3 -> 4 calls
        assert mock_summary_agent.run.call_count == max_iter + 1
        assert all(s == SUMMARY_RESP_1 for s in summaries)
        assert sample_ctx.retrieved_all is False  # Should still be False

    @pytest.mark.asyncio
    async def test_update_summary_stops_if_agent_returns_none(
        self, sample_ctx, mock_summary_agent
    ):
        """Test update_summary stops if the summary agent returns None."""
        workflow = UpdateSummaryWorkflow(max_iterations=5)
        sample_ctx.retrieved_all = False

        mock_summary_agent.run.side_effect = [
            MockRunResult(final_output=SUMMARY_RESP_1),
            None,  # Simulate agent failure or no more data
            MockRunResult(final_output=SUMMARY_RESP_2),  # Should not be reached
        ]

        summaries = await workflow.update_summary(ctx=sample_ctx)

        assert len(summaries) == 1  # Only the first summary before None
        assert summaries[0] == SUMMARY_RESP_1
        assert mock_summary_agent.run.call_count == 2  # Called twice (first success, second None)

    @pytest.mark.asyncio
    async def test_update_summary_no_iterations_if_already_retrieved(
        self, sample_ctx, mock_summary_agent
    ):
        """Test update_summary performs no iterations if retrieved_all is initially True."""
        workflow = UpdateSummaryWorkflow()
        sample_ctx.retrieved_all = True  # Start condition

        summaries = await workflow.update_summary(ctx=sample_ctx)

        assert len(summaries) == 0
        assert mock_summary_agent.run.call_count == 0

    @pytest.mark.asyncio
    async def test_merge_success(
        self, sample_ctx, mock_summary_merger_agent, mock_timeline_merger_agent
    ):
        """Test successful merging of summaries and timelines."""
        workflow = UpdateSummaryWorkflow()
        input_summaries = [SUMMARY_RESP_1, SUMMARY_RESP_2]

        # Configure mock returns for merger agents to return the actual response objects
        mock_summary_merger_agent.run_openai.return_value = MERGED_SUMMARY_ONLY_RESP
        mock_timeline_merger_agent.run_openai.return_value = MERGED_TIMELINE_RESP

        merged_result = await workflow.merge(ctx=sample_ctx, summaries=input_summaries)

        assert mock_summary_merger_agent.run_openai.call_count == 1
        mock_summary_merger_agent.run_openai.assert_called_once_with(input=input_summaries, context=sample_ctx)

        assert mock_timeline_merger_agent.run_openai.call_count == 1
        mock_timeline_merger_agent.run_openai.assert_called_once_with(input=input_summaries, context=sample_ctx)

        assert isinstance(merged_result, SummaryResponse)
        assert merged_result.summary == MERGED_SUMMARY_ONLY_RESP.summary
        assert merged_result.timeline == MERGED_TIMELINE_RESP.timeline
        assert merged_result.summary_changes == MERGED_SUMMARY_ONLY_RESP.changes
        assert merged_result.timeline_changes == MERGED_TIMELINE_RESP.changes
        # Check last doc info comes from the *last* input summary
        assert merged_result.last_document_id == input_summaries[-1].last_document_id
        assert merged_result.last_document_date == input_summaries[-1].last_document_date

    @pytest.mark.asyncio
    async def test_merge_one_agent_fails(
        self, sample_ctx, mock_summary_merger_agent, mock_timeline_merger_agent
    ):
        """Test merging when one of the merger agents returns None."""
        workflow = UpdateSummaryWorkflow()
        input_summaries = [SUMMARY_RESP_1]

        # Summary merger fails (returns None), timeline merger succeeds
        mock_summary_merger_agent.run_openai.return_value = None
        mock_timeline_merger_agent.run_openai.return_value = MockRunResult(final_output=MERGED_TIMELINE_RESP)

        merged_result = await workflow.merge(ctx=sample_ctx, summaries=input_summaries)

        # Should return the last summary
        assert merged_result.summary == input_summaries[-1].summary
        assert merged_result.timeline == input_summaries[-1].timeline
        assert merged_result.last_document_id == input_summaries[-1].last_document_id  # Default value
        assert merged_result.last_document_date == input_summaries[-1].last_document_date

    @pytest.mark.asyncio
    async def test_merge_both_agents_fail(
        self, sample_ctx, mock_summary_merger_agent, mock_timeline_merger_agent
    ):
        """Test merging when both merger agents return None."""
        workflow = UpdateSummaryWorkflow()
        input_summaries = [SUMMARY_RESP_1]

        mock_summary_merger_agent.run_openai.return_value = None
        mock_timeline_merger_agent.run_openai.return_value = None

        merged_result = await workflow.merge(ctx=sample_ctx, summaries=input_summaries)

        assert merged_result.summary == input_summaries[-1].summary
        assert merged_result.timeline == input_summaries[-1].timeline

    @pytest.mark.asyncio
    @patch.object(UpdateSummaryWorkflow, 'update_summary', new_callable=AsyncMock)
    @patch.object(UpdateSummaryWorkflow, 'merge', new_callable=AsyncMock)
    async def test_run_happy_path(
        self, mock_merge, mock_update_summary, mock_uuid, mock_tracing  # Ensure mocks are injected
    ):
        """Test the main run method orchestrates calls correctly."""
        workflow = UpdateSummaryWorkflow()

        # Configure mocks for sub-methods
        iterative_summaries = [SUMMARY_RESP_1, SUMMARY_RESP_2]
        mock_update_summary.return_value = iterative_summaries
        mock_merge.return_value = MERGED_SUMMARY_RESP

        # Call the run method
        final_summaries = await workflow.run(req=SAMPLE_REQ)

        # Assertions
        mock_update_summary.assert_called_once()
        # Check the context passed to update_summary
        call_args, call_kwargs = mock_update_summary.call_args
        passed_ctx = call_kwargs.get('ctx') or call_args[0]  # Get the context argument
        assert isinstance(passed_ctx, type(SAMPLE_REQ))
        # The context inside run is created using ConnyRequestSummaryCtx.from_summary(SAMPLE_REQ),
        # so its fields should match those of SAMPLE_REQ
        assert passed_ctx.request_id == SAMPLE_REQ.request_id

        mock_merge.assert_called_once()
        # Check arguments passed to merge
        call_args_merge, call_kwargs_merge = mock_merge.call_args
        assert call_kwargs_merge.get('ctx') == passed_ctx  # Should be the same context object
        assert call_kwargs_merge.get('summaries') == iterative_summaries

        # Check final result
        assert len(final_summaries) == 3  # Iterative summaries + merged summary
        assert final_summaries[0] == SUMMARY_RESP_1
        assert final_summaries[1] == SUMMARY_RESP_2
        assert final_summaries[2] == MERGED_SUMMARY_RESP

        # Check tracing and uuid usage (optional but good)
        mock_uuid.assert_called_once()

    @pytest.mark.asyncio
    @patch.object(UpdateSummaryWorkflow, 'update_summary', new_callable=AsyncMock)
    @patch.object(UpdateSummaryWorkflow, 'merge', new_callable=AsyncMock)
    async def test_run_no_iterative_summaries(
        self, mock_merge, mock_update_summary, mock_uuid, mock_tracing
    ):
        """Test run method when update_summary returns an empty list."""
        workflow = UpdateSummaryWorkflow()

        mock_update_summary.return_value = []  # Simulate no summaries generated

        final_summaries = await workflow.run(req=SAMPLE_REQ)

        mock_update_summary.assert_called_once()
        mock_merge.assert_not_called()  # Merge should not be called if no summaries
        assert final_summaries == []  # Expect an empty list back
