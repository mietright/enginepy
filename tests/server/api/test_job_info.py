import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from ant31box.models import Job
from ant31box.models import JobList as JobPayload
from fastapi.testclient import TestClient
from temporalio.client import WorkflowExecutionStatus, WorkflowHandle

from enginepy.models import AsyncResponse

# Sample Data
SAMPLE_WORKFLOW_ID = str(uuid.uuid4())
SAMPLE_WORKFLOW_NAME = "enginepy.temporal.workflows.echo:EchoWorkflow" # Example workflow
SAMPLE_SECRET_KEY = "test-secret-key-123"

@pytest.fixture
def client(app) -> TestClient:
    """Fixture to create a TestClient instance."""
    return TestClient(app)

@pytest.fixture
def mock_workflow_handle(mocker) -> MagicMock:
    """Mocks a Temporal WorkflowHandle."""
    handle = MagicMock(spec=WorkflowHandle)
    handle.describe = AsyncMock()
    handle.result = AsyncMock()
    handle.id = SAMPLE_WORKFLOW_ID
    return handle

@pytest.fixture
def mock_get_handler_job_info(mocker, mock_workflow_handle) -> AsyncMock:
    """Mocks the get_handler function within job_info.py."""
    # Mocks the one defined and used in job_info.py
    mock = AsyncMock(return_value=(mock_workflow_handle, MagicMock()))
    # Important: Patch the correct path where get_handler is looked up
    mocker.patch("enginepy.server.api.job_info.get_handler", mock)
    return mock

@pytest.fixture
def sample_async_response() -> AsyncResponse:
    """Creates a sample AsyncResponse for testing."""
    job = Job(uuid=SAMPLE_WORKFLOW_ID, name=SAMPLE_WORKFLOW_NAME, status="PENDING")
    payload = JobPayload(jobs=[job])
    # Use a fixed secret key for predictable signature generation/checking
    ar = AsyncResponse(payload=payload)
    return ar

# --- Test Cases ---

@pytest.mark.asyncio
async def test_status_completed_no_result(
    client: TestClient,
    mock_get_handler_job_info: AsyncMock,
    mock_workflow_handle: MagicMock,
    sample_async_response: AsyncResponse,
):
    """Test status endpoint for a completed workflow without requesting result."""
    # Configure mocks
    mock_describe = MagicMock()
    mock_describe.status = WorkflowExecutionStatus.COMPLETED
    mock_workflow_handle.describe.return_value = mock_describe

    # No need to generate signature as we don't request result
    response = client.post("/api/job/status?with_result=false", json=sample_async_response.model_dump())

    assert response.status_code == 200
    resp_data = AsyncResponse(**response.json())
    assert len(resp_data.payload.jobs) == 1
    job = resp_data.payload.jobs[0]
    assert job.uuid == SAMPLE_WORKFLOW_ID
    assert job.status == WorkflowExecutionStatus.COMPLETED.name
    assert job.result == {} # Default result is likely {}, not None

    mock_get_handler_job_info.assert_called_once_with(SAMPLE_WORKFLOW_ID, SAMPLE_WORKFLOW_NAME)
    mock_workflow_handle.describe.assert_called_once()
    mock_workflow_handle.result.assert_not_called()
    # Check if signature was generated on the response
    assert resp_data.signature is not None

@pytest.mark.asyncio
async def test_status_completed_with_result_valid_sig(
    client: TestClient,
    mock_get_handler_job_info: AsyncMock,
    mock_workflow_handle: MagicMock,
    sample_async_response: AsyncResponse,
):
    """Test status endpoint for a completed workflow, requesting result with valid signature."""
    # Configure mocks
    mock_describe = MagicMock()
    mock_describe.status = WorkflowExecutionStatus.COMPLETED
    mock_workflow_handle.describe.return_value = mock_describe
    mock_result = {"data": "workflow finished successfully"}
    mock_workflow_handle.result.return_value = mock_result

    # Generate signature on the input request
    sample_async_response.gen_signature()

    response = client.post("/api/job/status?with_result=true", json=sample_async_response.model_dump())

    assert response.status_code == 200
    resp_data = AsyncResponse(**response.json())
    assert len(resp_data.payload.jobs) == 1
    job = resp_data.payload.jobs[0]
    assert job.uuid == SAMPLE_WORKFLOW_ID
    assert job.status == WorkflowExecutionStatus.COMPLETED.name
    assert job.result == mock_result # Result should be populated

    mock_get_handler_job_info.assert_called_once_with(SAMPLE_WORKFLOW_ID, SAMPLE_WORKFLOW_NAME)
    mock_workflow_handle.describe.assert_called_once()
    mock_workflow_handle.result.assert_called_once() # Result should have been called
    assert resp_data.signature is not None
    # Response should also be signed
@pytest.mark.xfail
@pytest.mark.asyncio
async def test_status_completed_with_result_invalid_sig(
    client: TestClient,
    mock_get_handler_job_info: AsyncMock,
    mock_workflow_handle: MagicMock,
    sample_async_response: AsyncResponse,
):
    """Test status endpoint requesting result with an invalid/missing signature."""
    # Configure mocks
    mock_describe = MagicMock()
    mock_describe.status = WorkflowExecutionStatus.COMPLETED
    mock_workflow_handle.describe.return_value = mock_describe
    mock_result = {"data": "workflow finished successfully"}
    mock_workflow_handle.result.return_value = mock_result

    # DO NOT generate signature on the input request
    # sample_async_response.gen_signature()
     # Modify the signature to make it invalid
    body = sample_async_response.model_dump()
    body["signature"] = "invalid-signature"
    response = client.post("/api/job/status?with_result=true", json=body)
    res = response.json()
    assert response.status_code == 200 # Endpoint still succeeds, just doesn't fetch result
    resp_data = AsyncResponse(**res) # Remove signature for easier comparison
    assert len(resp_data.payload.jobs) == 1
    job = resp_data.payload.jobs[0]     # Remove signature for easier comparison
    assert job.uuid == SAMPLE_WORKFLOW_ID
    assert job.status == WorkflowExecutionStatus.COMPLETED.name
    assert job.result == {} # Result should NOT be populated, default is likely {}

    mock_get_handler_job_info.assert_called_once_with(SAMPLE_WORKFLOW_ID, SAMPLE_WORKFLOW_NAME)
    mock_workflow_handle.describe.assert_called_once()
    mock_workflow_handle.result.assert_not_called() # Result should NOT have been called
    assert resp_data.signature is not None # Response is still signed

@pytest.mark.asyncio
async def test_status_running(
    client: TestClient,
    mock_get_handler_job_info: AsyncMock,
    mock_workflow_handle: MagicMock,
    sample_async_response: AsyncResponse,
):
    """Test status endpoint for a running workflow."""
    # Configure mocks
    mock_describe = MagicMock()
    mock_describe.status = WorkflowExecutionStatus.RUNNING
    mock_workflow_handle.describe.return_value = mock_describe

    response = client.post("/api/job/status", json=sample_async_response.model_dump())

    assert response.status_code == 200
    resp_data = AsyncResponse(**response.json())
    assert len(resp_data.payload.jobs) == 1
    job = resp_data.payload.jobs[0]
    assert job.status == WorkflowExecutionStatus.RUNNING.name
    assert job.result == {} # Default result is likely {}, not None

    mock_get_handler_job_info.assert_called_once_with(SAMPLE_WORKFLOW_ID, SAMPLE_WORKFLOW_NAME)
    mock_workflow_handle.describe.assert_called_once()
    mock_workflow_handle.result.assert_not_called()
    assert resp_data.signature is not None

@pytest.mark.asyncio
async def test_status_not_found(
    client: TestClient,
    mock_get_handler_job_info: AsyncMock,
    mock_workflow_handle: MagicMock,
    sample_async_response: AsyncResponse,
):
    """Test status endpoint when the workflow is not found by describe."""
    # Configure mocks
    mock_describe = MagicMock()
    mock_describe.status = None # Simulate not found
    mock_workflow_handle.describe.return_value = mock_describe

    response = client.post("/api/job/status", json=sample_async_response.model_dump())

    assert response.status_code == 404
    assert "Workflow not found" in response.json()["detail"]["message"] # Check detail field

    mock_get_handler_job_info.assert_called_once_with(SAMPLE_WORKFLOW_ID, SAMPLE_WORKFLOW_NAME)
    mock_workflow_handle.describe.assert_called_once()
    mock_workflow_handle.result.assert_not_called()
