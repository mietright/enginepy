import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from temporalio.client import Client, WorkflowExecutionStatus, WorkflowHandle
from temporalio.common import WorkflowIDReusePolicy

from enginepy.agents.rental_classifier.models import (
    ClassificationRentalCtx,
    ClassificationRentalResponse,
    ClassificationRentalScore,
    ClassificationRentalType,
)
from enginepy.models import (
    AgentCaseSummaryWorkflowInput,
    AgentCaseSummaryWorkflowOutput,
    AgentClassifierWorkflowInput,
    AsyncResponse,
    ConnyRequestSummary,
    SummaryResponse,
    WorkflowInfo,
)
from enginepy.temporal.workflows.summary import AgentSummaryWorkflow
from enginepy.version import VERSION

# Sample Data
SAMPLE_REQ_ID = 123
SAMPLE_DOC_ID = 456
SAMPLE_WORKFLOW_ID_SUMMARY = f"summary-request-{SAMPLE_REQ_ID}"
SAMPLE_WORKFLOW_ID_CLASSIFY = f"classify-doc-{SAMPLE_DOC_ID}"
SUMMARY_WORKFLOW_NAME = "enginepy.temporal.workflows.summary:AgentSummaryWorkflow"
CLASSIFY_WORKFLOW_NAME = "enginepy.workflows.classifier_rental.ClassifierRentalWorkflow:run" # Although not used by temporal in current code

SAMPLE_CONNY_REQ = ConnyRequestSummary(request_id=SAMPLE_REQ_ID)
SAMPLE_SUMMARY_INPUT = AgentCaseSummaryWorkflowInput(context=SAMPLE_CONNY_REQ, input="test input")

SAMPLE_CLASSIFY_CTX = ClassificationRentalCtx(document_id=SAMPLE_DOC_ID, user_id="test-user", collection_id="test-col")
SAMPLE_CLASSIFY_INPUT = AgentClassifierWorkflowInput(context=SAMPLE_CLASSIFY_CTX, input="classify this text")
SAMPLE_CLASSIFY_RESULT = ClassificationRentalResponse(
    classification=ClassificationRentalScore(category=ClassificationRentalType.RENTAL_CONTRACT, confidence_score=0.9,
                    reasoning="test"),
    next_3_potential_categories=[]
)

SAMPLE_SUMMARY_RESULT_LIST = [SummaryResponse(summary="Final Summary",
                                              timeline="Final Timeline",
                                              last_document_date="2024-01-15T10:30:00Z",
                                                last_document_id="doc-1",
                                                summary_changes=[],
                                                timeline_changes=[])]
                                              
SAMPLE_SUMMARY_OUTPUT = AgentCaseSummaryWorkflowOutput(result=SAMPLE_SUMMARY_RESULT_LIST)


@pytest.fixture
def client(app) -> TestClient:
    """Fixture to create a TestClient instance."""
    return TestClient(app)

@pytest.fixture
def mock_tclient(mocker) -> AsyncMock:
    """Mocks the temporal client factory."""
    mock = AsyncMock()
    # Mock the start_workflow method specifically
    mock.start_workflow = AsyncMock(spec=Client.start_workflow)
    mocker.patch("enginepy.server.api.agents.tclient", return_value=mock)
    return mock

@pytest.fixture
def mock_workflow_handle(mocker) -> MagicMock:
    """Mocks a Temporal WorkflowHandle."""
    handle = MagicMock(spec=WorkflowHandle)
    handle.describe = AsyncMock()
    handle.result = AsyncMock()
    handle.id = SAMPLE_WORKFLOW_ID_SUMMARY # Default ID
    return handle

@pytest.fixture
def mock_get_handler(mocker, mock_workflow_handle) -> AsyncMock:
    """Mocks the get_handler utility function."""
    # Mocks the one imported and used in agents.py
    mock = AsyncMock(return_value=(mock_workflow_handle, MagicMock()))
    mocker.patch("enginepy.server.api.agents.get_handler", mock)
    return mock

@pytest.fixture
def mock_is_workflow_running(mocker) -> AsyncMock:
    """Mocks the is_workflow_running utility function."""
    mock = AsyncMock()
    mocker.patch("enginepy.server.api.agents.is_workflow_running", mock)
    return mock

@pytest.fixture
def mock_classifier_workflow(mocker) -> AsyncMock:
    """Mocks the ClassifierRentalWorkflow run method."""
    mock_run = AsyncMock(return_value=SAMPLE_CLASSIFY_RESULT)
    mocker.patch("enginepy.workflows.classifier_rental.ClassifierRentalWorkflow.run", mock_run)
    return mock_run


# --- Test Cases ---

def test_index(client: TestClient):
    """Test the root endpoint."""
    response = client.get("/api/agents/")
    assert response.status_code == 200
    assert response.json() == VERSION.to_dict()

def test_version(client: TestClient):
    """Test the version endpoint."""
    response = client.get("/api/agents/version")
    assert response.status_code == 200
    assert response.json() == VERSION.to_dict()

@pytest.mark.asyncio
async def test_classify(client: TestClient, mock_classifier_workflow: AsyncMock):
    """Test the classify endpoint."""
    response = client.post("/api/workflows/classify/sync", json=SAMPLE_CLASSIFY_INPUT.model_dump())

    assert response.status_code == 200
    # Compare Pydantic models directly for better handling of defaults/None
    mock_classifier_workflow.assert_called_once_with(input_str=SAMPLE_CLASSIFY_INPUT.input, ctx=SAMPLE_CLASSIFY_INPUT.context)

@pytest.mark.asyncio
async def test_create_summary_new_workflow(
    client: TestClient,
    mock_tclient: AsyncMock,
    mock_get_handler: AsyncMock,
    mock_is_workflow_running: AsyncMock,
    mock_workflow_handle: MagicMock,
):
    """Test creating a summary when the workflow is not running."""
    mock_is_workflow_running.return_value = False
    # Set the ID on the handle that start_workflow will return
    mock_workflow_handle.id = SAMPLE_WORKFLOW_ID_SUMMARY
    mock_tclient.start_workflow.return_value = mock_workflow_handle

    response = client.post("/api/agents/summary", json=SAMPLE_SUMMARY_INPUT.model_dump())

    assert response.status_code == 200
    resp_data = AsyncResponse(**response.json())
    assert len(resp_data.payload.jobs) == 1
    job = resp_data.payload.jobs[0]
    assert job.uuid == SAMPLE_WORKFLOW_ID_SUMMARY
    assert job.name == SUMMARY_WORKFLOW_NAME
    # Signature might be present or not depending on secret key, check if needed
    search_attrs = {"request_id": [str(SAMPLE_REQ_ID)]}
    mock_get_handler.assert_called_once_with(workflow_id=SAMPLE_WORKFLOW_ID_SUMMARY, workflow_name=SUMMARY_WORKFLOW_NAME)
    mock_is_workflow_running.assert_called_once_with(mock_workflow_handle)
    mock_tclient.start_workflow.assert_called_once()
    called_args, called_kwargs = mock_tclient.start_workflow.call_args
    assert called_kwargs['workflow'] is AgentSummaryWorkflow.run
    assert called_kwargs['search_attributes'] == search_attrs
    assert called_kwargs['id'] == SAMPLE_WORKFLOW_ID_SUMMARY
    assert called_kwargs['task_queue'] == "enginepy-queue"
    assert called_kwargs['id_reuse_policy'] == WorkflowIDReusePolicy.ALLOW_DUPLICATE


@pytest.mark.asyncio
async def test_create_summary_existing_workflow(
    client: TestClient,
    mock_tclient: AsyncMock,
    mock_get_handler: AsyncMock,
    mock_is_workflow_running: AsyncMock,
    mock_workflow_handle: MagicMock,
):
    """Test creating a summary when the workflow is already running."""
    mock_is_workflow_running.return_value = True
    mock_workflow_handle.id = SAMPLE_WORKFLOW_ID_SUMMARY # Ensure handle has the ID

    response = client.post("/api/agents/summary", json=SAMPLE_SUMMARY_INPUT.model_dump())

    assert response.status_code == 200
    resp_data = AsyncResponse(**response.json())
    assert len(resp_data.payload.jobs) == 1
    job = resp_data.payload.jobs[0]
    assert job.uuid == SAMPLE_WORKFLOW_ID_SUMMARY
    assert job.name == SUMMARY_WORKFLOW_NAME

    mock_get_handler.assert_called_once_with(workflow_id=SAMPLE_WORKFLOW_ID_SUMMARY, workflow_name=SUMMARY_WORKFLOW_NAME)
    mock_is_workflow_running.assert_called_once_with(mock_workflow_handle)
    mock_tclient.start_workflow.assert_not_called() # Crucial check

@pytest.mark.asyncio
async def test_get_summary_success_no_wait(
    client: TestClient,
    mock_get_handler: AsyncMock,
    mock_workflow_handle: MagicMock,
):
    """Test getting a summary result successfully without waiting."""
    # Configure mocks
    mock_describe = MagicMock()
    mock_describe.status = WorkflowExecutionStatus.COMPLETED
    mock_workflow_handle.describe.return_value = mock_describe
    mock_workflow_handle.result.return_value = SAMPLE_SUMMARY_OUTPUT

    response = client.get(f"/api/agents/summary/{SAMPLE_WORKFLOW_ID_SUMMARY}")

    assert response.status_code == 200
    expected_output = SAMPLE_SUMMARY_OUTPUT.model_copy()
    expected_output.workflow_info = WorkflowInfo(wid=SAMPLE_WORKFLOW_ID_SUMMARY, name=SUMMARY_WORKFLOW_NAME)
    # Compare Pydantic models directly
    assert AgentCaseSummaryWorkflowOutput(**response.json()) == expected_output

    mock_get_handler.assert_called_once_with(workflow_id=SAMPLE_WORKFLOW_ID_SUMMARY, workflow_name=SUMMARY_WORKFLOW_NAME)
    mock_workflow_handle.describe.assert_called_once()
    # Check result() was called without timeout args
    mock_workflow_handle.result.assert_called_once_with()

@pytest.mark.asyncio
@patch('asyncio.wait_for') # Patch asyncio.wait_for directly
async def test_get_summary_success_with_wait(
    mock_wait_for: AsyncMock, # Comes from patch
    client: TestClient,
    mock_get_handler: AsyncMock,
    mock_workflow_handle: MagicMock,
):
    """Test getting a summary result successfully with waiting."""
    wait_time = 5
    # Configure mocks
    mock_describe = MagicMock()
    mock_describe.status = WorkflowExecutionStatus.RUNNING # Assume it's running initially
    mock_workflow_handle.describe.return_value = mock_describe
    # Mock the result that wait_for will eventually return
    mock_wait_for.return_value = SAMPLE_SUMMARY_OUTPUT

    response = client.get(f"/api/agents/summary/{SAMPLE_WORKFLOW_ID_SUMMARY}?wait_for={wait_time}")

    assert response.status_code == 200
    expected_output = SAMPLE_SUMMARY_OUTPUT.model_copy()
    expected_output.workflow_info = WorkflowInfo(wid=SAMPLE_WORKFLOW_ID_SUMMARY, name=SUMMARY_WORKFLOW_NAME)
    # Compare Pydantic models directly
    assert AgentCaseSummaryWorkflowOutput(**response.json()) == expected_output

    mock_get_handler.assert_called_once_with(workflow_id=SAMPLE_WORKFLOW_ID_SUMMARY, workflow_name=SUMMARY_WORKFLOW_NAME)
    mock_workflow_handle.describe.assert_called_once()
    # Check that wait_for was called correctly, wrapping handler.result()
    mock_wait_for.assert_called_once()
    # Check the arguments passed to wait_for
    call_args, call_kwargs = mock_wait_for.call_args
    assert len(call_args) == 1 # The awaitable
    assert call_kwargs == {'timeout': wait_time}
    # Check that the awaitable passed was handler.result with the correct rpc_timeout
    mock_workflow_handle.result.assert_called_once_with(rpc_timeout=timedelta(seconds=wait_time))

@pytest.mark.asyncio
async def test_get_summary_not_found(
    client: TestClient,
    mock_get_handler: AsyncMock,
    mock_workflow_handle: MagicMock,
):
    """Test getting a summary when the workflow is not found."""
    mock_describe = MagicMock()
    mock_describe.status = None # Simulate not found
    mock_workflow_handle.describe.return_value = mock_describe

    response = client.get(f"/api/agents/summary/{SAMPLE_WORKFLOW_ID_SUMMARY}")

    assert response.status_code == 404
    assert "Workflow not found" in response.json()["detail"]["message"] # Check 'message' field
    mock_get_handler.assert_called_once_with(workflow_id=SAMPLE_WORKFLOW_ID_SUMMARY, workflow_name=SUMMARY_WORKFLOW_NAME)
    mock_workflow_handle.describe.assert_called_once()
    mock_workflow_handle.result.assert_not_called()

@pytest.mark.asyncio
@patch('asyncio.wait_for', side_effect=asyncio.TimeoutError) # Patch wait_for to raise TimeoutError
async def test_get_summary_wait_timeout(
    mock_wait_for: AsyncMock, # Comes from patch
    client: TestClient,
    mock_get_handler: AsyncMock,
    mock_workflow_handle: MagicMock,
):
    """Test getting a summary with wait_for results in a timeout."""
    wait_time = 1
    # Configure mocks
    mock_describe = MagicMock()
    mock_describe.status = WorkflowExecutionStatus.RUNNING # Still running
    mock_workflow_handle.describe.return_value = mock_describe

    response = client.get(f"/api/agents/summary/{SAMPLE_WORKFLOW_ID_SUMMARY}?wait_for={wait_time}")

    assert response.status_code == 500 # Unexpected exception
    assert "Workflow did not complete within the specified timeout" in response.json()["detail"]["message"] # Check detail field

    mock_get_handler.assert_called_once_with(workflow_id=SAMPLE_WORKFLOW_ID_SUMMARY, workflow_name=SUMMARY_WORKFLOW_NAME)
    mock_workflow_handle.describe.assert_called_once()
    # Check wait_for was called
    mock_wait_for.assert_called_once()
    # Check handler.result was called within wait_for
    mock_workflow_handle.result.assert_called_once_with(rpc_timeout=timedelta(seconds=wait_time))
