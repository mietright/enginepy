import uuid
from datetime import timedelta

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

# Import models and workflows
from enginepy.agents.case_summary.models import ConnyRequestSummary, SummaryResponse
from enginepy.models import AgentCaseSummaryWorkflowInput, AgentCaseSummaryWorkflowOutput
from enginepy.temporal.workflows.summary import AgentSummaryWorkflow

# --- Mock Activity ---

# Define expected output structure for the mock activity
MOCK_SUMMARY_OUTPUT = AgentCaseSummaryWorkflowOutput(
    result=[SummaryResponse(summary="Mocked Summary Result",
                            timeline="Mocked Timeline Result",
                            summary_changes=[],
                            timeline_changes=[],
                            last_document_id="mock-doc-id",
                            last_document_date="2024-01-15T10:30:00Z")],
)

@activity.defn(name="agent_summary")
async def agent_summary_mock(data: AgentCaseSummaryWorkflowInput) -> AgentCaseSummaryWorkflowOutput:
    """Mock implementation of the agent_summary activity."""
    # Optionally add assertions here about the input 'data'
    assert isinstance(data, AgentCaseSummaryWorkflowInput)
    assert data.context.request_id == 12345
    return MOCK_SUMMARY_OUTPUT

# --- Workflow Test ---

@pytest.mark.asyncio
async def test_agent_summary_workflow(client: Client):
    """Test the AgentSummaryWorkflow executes the activity."""
    task_queue_name = str(uuid.uuid4())
    workflow_id = f"test-summary-wf-{uuid.uuid4()}"

    # Input for the workflow
    workflow_input = AgentCaseSummaryWorkflowInput(
        context=ConnyRequestSummary(request_id=12345),
        input="Summarize this case."
    )

    async with Worker(
        client,
        task_queue=task_queue_name,
        workflows=[AgentSummaryWorkflow],
        activities=[agent_summary_mock],
    ):
        # Execute the workflow
        result = await client.execute_workflow(
            AgentSummaryWorkflow.run,
            workflow_input,
            id=workflow_id,
            task_queue=task_queue_name,
            execution_timeout=timedelta(seconds=10),
            run_timeout=timedelta(seconds=5),
        )

        # Assertions
        assert isinstance(result, AgentCaseSummaryWorkflowOutput)
        assert result == MOCK_SUMMARY_OUTPUT
