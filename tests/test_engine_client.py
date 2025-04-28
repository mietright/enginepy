import json  # Add json import for data serialization check
from datetime import datetime  # Added
from unittest.mock import AsyncMock, call  # Added for mocking async method

import pytest
import pytest_asyncio
from aiohttp import ClientResponseError, ClientTimeout
from aioresponses import aioresponses

from enginepy import __version__
from enginepy.engine_client import EngineClient
from enginepy.models import (
    AgentClassifierWorkflowOutput,
    AwsClassifierResult,
    AwsInference,
    AwsJobDescribe,
    ClassificationRentalResponse,
    ClassificationRentalScore,
    Content,
    DocsQuery,
    DocsResponse,
    EngineField,
    EngineRequest,
    EngineTrigger,
    ManagerEnum,
    OutputFormatEnum,
    WithContentMode,
)


@pytest.fixture
def test_endpoint() -> str:
    """Fixture for the test API endpoint."""
    return "http://test-engine.local"


@pytest.fixture
def test_token() -> str:
    """Fixture for the test API token."""
    return "test-token-123"


@pytest.fixture
def doc_id() -> int:
    """Fixture for a test document ID."""
    return 123


@pytest.fixture
def request_id() -> int:
    """Fixture for a test request ID."""
    return 456


@pytest.fixture
def trigger_id() -> str:
    """Fixture for a test trigger ID."""
    return "trigger-abc"


@pytest.fixture
def expected_user_agent() -> str:
    """Fixture for the expected User-Agent header."""
    # Correct User-Agent format based on BaseClient behavior
    return f"ant31box-cli/engine-{__version__}"


@pytest_asyncio.fixture
async def client(test_endpoint: str, test_token: str) -> EngineClient:
    """Fixture to create an EngineClient instance for testing."""
    instance = EngineClient(endpoint=test_endpoint, token=test_token)
    yield instance
    # Clean up the client session after tests if necessary
    await instance.session.close()


@pytest.mark.asyncio
async def test_health_success(client: EngineClient, test_endpoint: str, test_token: str, expected_user_agent: str):
    """Test successful health check."""
    with aioresponses() as m:
        m.get(f"{test_endpoint}/_health", payload={"status": "ok"}, status=200)
        response = await client.health()
        assert response == {"status": "ok"}
        expected_timeout = ClientTimeout(total=10)
        # Match the headers exactly as observed in the error output
        expected_headers = {
            "Accept": "*/*",
            "token": test_token,
            "User-Agent": expected_user_agent,
            # BaseClient adds Content-Type: application/json by default, even for GET
            # This needs to be included in the assertion to match the recorded call.
            "Content-Type": "application/json",
        }
        m.assert_called_once_with(
            f"{test_endpoint}/_health",
            method="GET",
            headers=expected_headers,
            ssl=False,
            timeout=expected_timeout,
        )


@pytest.mark.asyncio
async def test_health_failure(client: EngineClient, test_endpoint: str):
    """Test failed health check."""
    with aioresponses() as m:
        m.get(f"{test_endpoint}/_health", status=500, payload={"error": "internal server error"})
        with pytest.raises(ClientResponseError) as exc_info:
            await client.health()
        assert exc_info.value.status == 500


@pytest.mark.asyncio
async def test_update_doc_success(client: EngineClient, test_endpoint: str, test_token: str, doc_id: int, expected_user_agent: str):
    """Test successful document update."""
    ocr_pages = ["page 1 text", "page 2 text"]
    pdf_url = "http://example.com/doc.pdf"
    expected_payload = {
        "document_id": str(doc_id),
        "ocr": ocr_pages,
        "searchable_pdf_url": pdf_url,
    }

    with aioresponses() as m:
        m.post(f"{test_endpoint}/api/zieb/documents/ocr", status=200)
        result = await client.update_doc(doc_id, ocr_pages, pdf_url)
        assert result is True
        expected_timeout = ClientTimeout(total=30)
        # Match headers exactly, including Content-Type added for JSON payload
        expected_headers = {
            "Accept": "*/*",
            "token": test_token,
            "Content-Type": "application/json",
            "User-Agent": expected_user_agent,
        }
        m.assert_called_once_with(
            f"{test_endpoint}/api/zieb/documents/ocr",
            method="POST",
            json=expected_payload,
            headers=expected_headers,
            params={},
            ssl=False,
            timeout=expected_timeout,
        )


@pytest.mark.asyncio
async def test_update_doc_failure(client: EngineClient, test_endpoint: str, doc_id: int):
    """Test failed document update."""
    with aioresponses() as m:
        m.post(f"{test_endpoint}/api/zieb/documents/ocr", status=400)
        with pytest.raises(ClientResponseError) as exc_info:
            await client.update_doc(doc_id, ["page text"])
        assert exc_info.value.status == 400


# Add more tests for other methods (update_doc_suggestions, action_trigger, etc.)
# following a similar pattern:
# 1. Define input data (models).
# 2. Use `aioresponses` context manager.
# 3. Mock the expected URL, method, status, and optionally payload.
# 4. Call the client method.
# 5. Assert the response or raised exception.
# 6. Use `m.assert_called_once_with(...)` to verify the request details (URL, method, headers, json/data, params).


@pytest.mark.asyncio
async def test_action_trigger_success(client: EngineClient, test_endpoint: str, test_token: str, trigger_id: str, request_id: int, expected_user_agent: str):
    """Test successful action trigger."""
    trigger = EngineTrigger(
        trigger_id=trigger_id,
        request_id=request_id,
        name="test_trigger",
        client="test_client",
        attempt=2
    )
    # Params should match the types recorded by aioresponses (int for request_id/attempt)
    expected_params = {"request_id": request_id, "client": "test_client", "attempt": 2}
    response_payload = {"status": "processed"}
    # Use the exact URL including params for matching, or keep regex if preferred
    # url_pattern = re.compile(f"^{test_endpoint}/api/admin/action_triggers/{trigger_id}(\\?.*)?$")
    expected_url = f"{test_endpoint}/api/admin/action_triggers/{trigger_id}"
    # Construct the full URL with query parameters for mocking
    from urllib.parse import urlencode
    full_expected_url = f"{expected_url}?{urlencode(expected_params)}"


    with aioresponses() as m:
        # Mock the full URL including query parameters
        m.put(full_expected_url, status=200, payload=response_payload)
        updated_trigger = await client.action_trigger(trigger)

        assert updated_trigger is trigger
        assert updated_trigger.status == response_payload
        expected_timeout = ClientTimeout(total=30)
        # Match headers exactly, including Content-Type for form
        expected_headers = {
            "Accept": "*/*",
            "token": test_token,
            "Content-Type": "application/x-www-form-urlencoded", # Set by client.headers("form")
            "User-Agent": expected_user_agent,
        }
        m.assert_called_once_with(
            expected_url, # Use base URL
            method="PUT",
            params=expected_params, # Assert params separately
            headers=expected_headers,
            ssl=False,
            timeout=expected_timeout,
            data=None, # Explicitly assert data is None, matching aioresponses recording
        )


@pytest.mark.asyncio
async def test_action_trigger_failure(client: EngineClient, test_endpoint: str, trigger_id: str, request_id: int):
    """Test failed action trigger."""
    trigger = EngineTrigger(trigger_id=trigger_id, request_id=request_id) # client='enginepy', attempt=1 are defaults
    expected_url = f"{test_endpoint}/api/admin/action_triggers/{trigger_id}"
    # Define expected params based on trigger defaults to match the actual client call
    expected_params = {"request_id": str(request_id), "client": "enginepy", "attempt": "1"}
    # Construct the full URL with query parameters for mocking
    from urllib.parse import urlencode
    full_expected_url = f"{expected_url}?{urlencode(expected_params)}"


    with aioresponses() as m:
        # Mock the full URL including query parameters
        m.put(full_expected_url, status=404)
        with pytest.raises(ClientResponseError) as exc_info:
            await client.action_trigger(trigger)
        assert exc_info.value.status == 404


@pytest.mark.asyncio
async def test_create_request_success(client: EngineClient, test_endpoint: str, test_token: str, expected_user_agent: str):
    """Test successful request creation."""
    req = EngineRequest(
        product="prod_a",
        funnel="funnel_b",
        fields=[EngineField(field="field1", answer="value1")] # type defaults to "string"
    )
    # Match the exact data payload recorded by aioresponses in the previous failure.
    # This indicates the client's model_dump excluded defaults like 'type', 'documents', 'documents_presign'.
    expected_data = {
        "product": "prod_a",
        "funnel": "funnel_b",
        # The actual 'fields' JSON string did not contain 'type'.
        "fields": json.dumps([{"field": "field1", "answer": "value1"}], sort_keys=True, default=str),
        # 'documents' and 'documents_presign' were not in the actual payload.
        "request_id": None, # This was present in the actual payload.
    }
    response_payload = {"request_id": 789, "status": "created"}
    expected_url = f"{test_endpoint}/api/admin/data_source"

    with aioresponses() as m:
        m.post(expected_url, status=201, payload=response_payload)
        response = await client.create_request(req)
        assert response == response_payload
        expected_timeout = ClientTimeout(total=30)
        # Match headers exactly, including Content-Type for form
        expected_headers = {
            "Accept": "*/*",
            "token": test_token,
            "Content-Type": "application/x-www-form-urlencoded", # Set by client.headers("form")
            "User-Agent": expected_user_agent,
        }
        m.assert_called_once_with(
            expected_url,
            method="POST",
            data=expected_data,
            headers=expected_headers,
            ssl=False,
            timeout=expected_timeout,
        )


@pytest.mark.asyncio
async def test_update_request_success(client: EngineClient, test_endpoint: str, test_token: str, request_id: int, expected_user_agent: str):
    """Test successful request update."""
    req = EngineRequest(
        product="prod_a_updated",
        funnel="funnel_b_updated",
        fields=[EngineField(field="field1", answer="value1_updated")] # type defaults to "string"
    )
    # Match the exact data payload recorded by aioresponses in the previous failure.
    # This indicates the client's model_dump excluded defaults like 'type', 'documents', 'documents_presign'.
    expected_data = {
        "product": "prod_a_updated",
        "funnel": "funnel_b_updated",
        # The actual 'fields' JSON string did not contain 'type'.
        "fields": json.dumps([{"field": "field1", "answer": "value1_updated"}], sort_keys=True, default=str),
        # 'documents' and 'documents_presign' were not in the actual payload.
        "request_id": request_id, # This was present in the actual payload.
    }
    response_payload = {"status": "updated"}
    expected_url = f"{test_endpoint}/api/admin/data_source"

    with aioresponses() as m:
        m.put(expected_url, status=200, payload=response_payload)
        response = await client.update_request(request_id, req)
        assert response == response_payload
        expected_timeout = ClientTimeout(total=30)
        # Match headers exactly, including Content-Type for form
        expected_headers = {
            "Accept": "*/*",
            "token": test_token,
            "Content-Type": "application/x-www-form-urlencoded", # Set by client.headers("form")
            "User-Agent": expected_user_agent,
        }
        m.assert_called_once_with(
            expected_url,
            method="PUT",
            data=expected_data,
            params={}, # Empty params for PUT in client code
            headers=expected_headers,
            ssl=False,
            timeout=expected_timeout,
        )


@pytest.mark.asyncio
async def test_update_insights_success(client: EngineClient, test_endpoint: str, test_token: str, expected_user_agent: str):
    """Test successful insights update."""
    docs_resp = DocsResponse(
        # Ensure query has defaults matching model_dump(exclude_none/unset) behavior
        query=DocsQuery(limit=100, mode=WithContentMode.SUMMARY, vectordb=ManagerEnum.NONE, output=OutputFormatEnum.JSON),
        docs=[Content(metadata={"doc_id": "doc1"}, full="content1")]
    )
    # The error message actually showed the recorded call included the full query dict.
    # This implies the defaults were *not* excluded by exclude_unset=True in the client call.
    # We need to match this structure in our expected payload for the assertion.
    expected_payload = {
        'docs': [{'metadata': {'doc_id': 'doc1'}, 'full': 'content1'}],
         # Include the full query dict with defaults serialized as strings, matching the recorded call.
        'query': {'limit': 100, 'mode': 'summary', 'vectordb': 'none', 'output': 'json'}
    }


    response_payload = {"message": "Insights updated"}
    expected_url = f"{test_endpoint}/api/insights"

    with aioresponses() as m:
        m.post(expected_url, status=200, payload=response_payload)
        response = await client.update_insights(docs_resp)
        assert response == response_payload
        expected_timeout = ClientTimeout(total=30)
        # Match headers exactly, including Content-Type for JSON
        expected_headers = {
            "Accept": "*/*",
            "token": test_token,
            "Content-Type": "application/json",
            "User-Agent": expected_user_agent,
        }
        m.assert_called_once_with(
            expected_url,
            method="POST",
            json=expected_payload,
            params={},
            headers=expected_headers,
            ssl=False,
            timeout=expected_timeout,
        )


@pytest.mark.asyncio
async def test_update_doc_suggestions_aws_success(client: EngineClient, test_endpoint: str, test_token: str, expected_user_agent: str):
    """Test successful document suggestions update using AwsClassifierResult."""
    aws_result = AwsClassifierResult(
        job=AwsJobDescribe(id="job-123", submit_time=datetime.now(), end_time=datetime.now()),
        inference=[AwsInference(line="doc1", classes=[])],
        model="aws-model-v1"
    )
    # Match client behavior: model_dump without by_alias=True uses serialization_alias
    expected_payload = aws_result.model_dump(exclude_none=True, exclude_unset=True)
    response_payload = {"message": "Suggestions updated via AWS"}
    expected_url = f"{test_endpoint}/api/zieb/documents/update_suggestions"

    with aioresponses() as m:
        m.post(expected_url, status=200, payload=response_payload)
        response = await client.update_doc_suggestions(aws_result)
        assert response == response_payload
        expected_timeout = ClientTimeout(total=30)
        expected_headers = {
            "Accept": "*/*",
            "token": test_token,
            "Content-Type": "application/json",
            "User-Agent": expected_user_agent,
        }
        m.assert_called_once_with(
            expected_url,
            method="POST",
            json=expected_payload,
            params={},
            headers=expected_headers,
            ssl=False,
            timeout=expected_timeout,
        )


@pytest.mark.asyncio
async def test_update_doc_suggestions_agent_success(client: EngineClient, test_endpoint: str, test_token: str, expected_user_agent: str):
    """Test successful document suggestions update using AgentClassifierWorkflowOutput."""
    agent_result = AgentClassifierWorkflowOutput(
        result=ClassificationRentalResponse(
            classification=ClassificationRentalScore(category="cat1", reasoning="reason1", confidence_score=0.9)
        )
    )
    expected_payload = agent_result.model_dump(exclude_none=True, exclude_unset=True)
    response_payload = {"message": "Suggestions updated via Agent"}
    expected_url = f"{test_endpoint}/api/zieb/documents/update_suggestions"

    with aioresponses() as m:
        m.post(expected_url, status=200, payload=response_payload)
        response = await client.update_doc_suggestions(agent_result)
        assert response == response_payload
        expected_timeout = ClientTimeout(total=30)
        expected_headers = {
            "Accept": "*/*",
            "token": test_token,
            "Content-Type": "application/json",
            "User-Agent": expected_user_agent,
        }
        m.assert_called_once_with(
            expected_url,
            method="POST",
            json=expected_payload,
            params={},
            headers=expected_headers,
            ssl=False,
            timeout=expected_timeout,
        )


@pytest.mark.asyncio
async def test_update_doc_suggestions_failure(client: EngineClient, test_endpoint: str):
    """Test failed document suggestions update."""
    # Use a simple input for failure test
    agent_result = AgentClassifierWorkflowOutput(
        result=ClassificationRentalResponse(
            classification=ClassificationRentalScore(category="cat1", reasoning="reason1", confidence_score=0.9)
        )
    )
    expected_url = f"{test_endpoint}/api/zieb/documents/update_suggestions"

    with aioresponses() as m:
        m.post(expected_url, status=400, payload={"error": "bad input"})
        with pytest.raises(ClientResponseError) as exc_info:
            await client.update_doc_suggestions(agent_result)
        assert exc_info.value.status == 400


@pytest.mark.asyncio
async def test_action_triggers_success(client: EngineClient, request_id: int):
    """Test successful processing of multiple triggers via action_triggers."""
    triggers_input = [
        {"name": "trigger1", "trigger_id": "tid1"},
        {"name": "trigger2", "trigger_id": "tid2", "attempt": "3"}, # Test string attempt conversion
        {"name": "trigger3", "trigger_id": "tid3", "attempt": 4}, # Test int attempt
    ]

    # Expected EngineTrigger objects to be created and passed to action_trigger
    expected_trigger1 = EngineTrigger(request_id=request_id, name="trigger1", trigger_id="tid1", attempt=1) # Default attempt
    expected_trigger2 = EngineTrigger(request_id=request_id, name="trigger2", trigger_id="tid2", attempt=3)
    expected_trigger3 = EngineTrigger(request_id=request_id, name="trigger3", trigger_id="tid3", attempt=4)

    # Mock return values for action_trigger (can be the same objects or modified ones)
    # Let's simulate action_trigger adding a status
    mock_return1 = EngineTrigger(request_id=request_id, name="trigger1", trigger_id="tid1", attempt=1, status={"result": "ok1"})
    mock_return2 = EngineTrigger(request_id=request_id, name="trigger2", trigger_id="tid2", attempt=3, status={"result": "ok2"})
    mock_return3 = EngineTrigger(request_id=request_id, name="trigger3", trigger_id="tid3", attempt=4, status={"result": "ok3"})

    # Mock the action_trigger method using AsyncMock
    client.action_trigger = AsyncMock(side_effect=[mock_return1, mock_return2, mock_return3])

    results = await client.action_triggers(request_id, triggers_input)

    # Verify action_trigger was called correctly for each input trigger
    expected_calls = [
        call(expected_trigger1),
        call(expected_trigger2),
        call(expected_trigger3),
    ]
    client.action_trigger.assert_has_calls(expected_calls, any_order=False) # asyncio.gather preserves order
    assert client.action_trigger.call_count == len(triggers_input)

    # Verify the results returned by action_triggers match the mocked return values
    assert results == [mock_return1, mock_return2, mock_return3]


# TODO: Add tests verifying specific header content (e.g., token, content-type) more explicitly if needed.
# TODO: Add tests for edge cases (e.g., empty lists, optional parameters).
