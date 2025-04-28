import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.testing import ActivityEnvironment
from temporalio.worker import Worker

from enginepy.agents.case_summary.models import ConnyRequestSummary, SummaryResponse
from enginepy.models import AnyData
from enginepy.temporal.activities import (
    AgentCaseSummaryWorkflowInput,
    AgentCaseSummaryWorkflowOutput,
    agent_summary,
    echo,
)
from enginepy.temporal.workflows.echo import EchoAsyncWorkflow

logger = logging.getLogger(__name__)

# A list of tuples where each tuple contains:
# - The activity function
# - The order amount
# - The expected result string
activity_test_data = [
    ({"works": None, "echo": True} ),
    ({"pages": ["a", "b"], "parts": 3} ),
]
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data", activity_test_data
)
async def test_echo_activity(data):
    activity_environment = ActivityEnvironment()
    model = AnyData(**data)
    result = activity_environment.run(echo, model)
    assert result.model_dump() == data



@pytest.mark.asyncio
@patch("enginepy.temporal.activities.UpdateSummaryWorkflow")
async def test_agent_summary_activity(mock_update_workflow_cls):
    """Test the agent_summary activity."""
    activity_environment = ActivityEnvironment()

    # Mock the UpdateSummaryWorkflow instance and its run method
    mock_workflow_instance = AsyncMock()
    mock_run_result = [SummaryResponse(
         summary="Final Summary",
         timeline="Final Timeline",
         summary_changes=[],
         timeline_changes=[],
         last_document_id="",
         last_document_date=""
    )]
    mock_workflow_instance.run.return_value = mock_run_result
    mock_update_workflow_cls.return_value = mock_workflow_instance

    # Prepare input data
    input_data = AgentCaseSummaryWorkflowInput(
        context=ConnyRequestSummary(request_id=123), input="Initial query"
    )

    # Run the activity
    result = await activity_environment.run(agent_summary, input_data)

    # Assertions
    assert isinstance(result, AgentCaseSummaryWorkflowOutput)
    assert result.result == mock_run_result
    mock_update_workflow_cls.assert_called_once()  # Check if workflow class was instantiated
    mock_workflow_instance.run.assert_called_once_with(input_data.context)  # Check run was called with context

# async def test_echo_workflow(client: Client):
#     task_queue_name = str(uuid.uuid4())
#     logger.info(client.data_converter)
#     async with Worker(
#         client,
#         task_queue=task_queue_name,
#         workflows=[EchoWorkflow],
#         activities=[echo],
#         activity_executor=ThreadPoolExecutor(10),
#     ):
#         assert (await client.execute_workflow(
#             EchoWorkflow.run,
#             AnyData(**{'Hello': "World!"}),
#             id=str(uuid.uuid4()),
#             task_queue=task_queue_name,
#             run_timeout=timedelta(seconds=3),

#         )).model_dump()['Hello'] == "World!"


# async def test_aecho_workflow(client: Client):
#     task_queue_name = str(uuid.uuid4())

#     async with Worker(
#         client,
#         task_queue=task_queue_name,
#         workflows=[EchoAsyncWorkflow],
#         activities=[aecho],
#     ):
#         res = (await client.execute_workflow(
#             EchoAsyncWorkflow.run,
#             {'Hello': "World!"},
#             id=str(uuid.uuid4()),
#             task_queue=task_queue_name,
#             run_timeout=timedelta(seconds=3),
#         ))
#         assert 'Hello' in res
#         assert res['Hello'] == "World!"




@activity.defn(name="aecho")
async def aecho_mocked(model: dict[str, Any]) -> dict[str, Any]:
    _ = model
    return {"greeting": "Hello from mocked activity!"}


async def test_mock_activity(client: Client):
    task_queue_name = str(uuid.uuid4())
    async with Worker(
        client,
        task_queue=task_queue_name,
        activity_executor=ThreadPoolExecutor(10),
        workflows=[EchoAsyncWorkflow],
        activities=[aecho_mocked],
    ):
        assert (await client.execute_workflow(
            EchoAsyncWorkflow.run,
            {'ignore': "World"},
            id=str(uuid.uuid4()),
            run_timeout=timedelta(seconds=3),
            task_queue=task_queue_name,
        ))['greeting'] == "Hello from mocked activity!"
