import json
import os
from collections.abc import AsyncIterator
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, call

import httpx
import pytest
import pytest_asyncio
import respx

from enginepy import __version__
from enginepy.config import EngineConfigSchema, EngineTokensConfigSchema
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
    DocumentUrlResponse,
    EngineField,
    EngineRequest,
    EngineTrigger,
    EngineTypeEnum,
    ManagerEnum,
    OutputFormatEnum,
    RequestDocumentsResponse,
    WithContentMode,
)
from enginepy.telli.models import TelliWebhook


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
async def client(test_endpoint: str, test_token: str) -> AsyncIterator[EngineClient]:
    """Fixture to create an EngineClient instance for testing."""
    instance = EngineClient(endpoint=test_endpoint, token=test_token)
    yield instance
    await instance.session.aclose()


@pytest.mark.asyncio
async def test_set_token(client: EngineClient, test_token: str):
    """Test that set_token updates the client instance's token with instance-wide override."""
    assert client.token == test_token
    new_token = "a-different-token"
    client.set_token(new_token)
    assert client.token == new_token
    assert client._override_token == new_token


@pytest.mark.asyncio
async def test_set_token_overrides_specific_token_when_no_key_given(
    test_endpoint: str, trigger_id: str, request_id: int
):
    """
    Tests that set_token() without a key parameter overrides all tokens for this client instance,
    including specific tokens like admin.
    """
    admin_token = "original-admin-token"
    new_token = "new-global-override-token"

    cfg = EngineConfigSchema(
        endpoint=test_endpoint,
        token="default-fallback-token",
        tokens=EngineTokensConfigSchema(admin=admin_token),
    )

    client = EngineClient(config=cfg)
    client.set_token(new_token)

    trigger = EngineTrigger(trigger_id=trigger_id, request_id=request_id)
    expected_url = f"{test_endpoint}/api/admin/action_triggers/{trigger_id}"

    with respx.mock() as mock:
        mock.put(url__regex=rf".*{trigger_id}.*").mock(return_value=httpx.Response(200, json={"status": "ok"}))
        await client.action_trigger(trigger)

        assert len(mock.calls) > 0
        req = mock.calls.last.request
        assert req.headers["token"] == new_token
        assert req.headers["token"] != admin_token

    await client.session.aclose()


@pytest.mark.asyncio
async def test_set_token_with_key_updates_specific_token(test_endpoint: str, trigger_id: str, request_id: int):
    """
    Tests that set_token(token, key) updates a specific token in config.tokens.
    """
    original_admin_token = "original-admin-token"
    new_admin_token = "new-admin-token"

    cfg = EngineConfigSchema(
        endpoint=test_endpoint,
        token="default-fallback-token",
        tokens=EngineTokensConfigSchema(admin=original_admin_token),
    )

    client = EngineClient(config=cfg)
    client.set_token(new_admin_token, key="admin")

    trigger = EngineTrigger(trigger_id=trigger_id, request_id=request_id)

    with respx.mock() as mock:
        mock.put(url__regex=rf".*{trigger_id}.*").mock(return_value=httpx.Response(200, json={"status": "ok"}))
        await client.action_trigger(trigger)

        assert mock.called
        req = mock.calls.last.request
        assert req.headers["token"] == new_admin_token

    await client.session.aclose()


@pytest.mark.asyncio
async def test_headers_with_extra(client: EngineClient, test_token: str, expected_user_agent: str):
    """Test that the headers method includes extra headers."""
    extra_headers = {"X-Custom-Header": "CustomValue"}
    headers = client.headers(extra=extra_headers)

    assert headers["X-Custom-Header"] == "CustomValue"
    assert headers["token"] == test_token
    assert headers["User-Agent"] == expected_user_agent
    assert headers["Accept"] == "*/*"


@pytest.mark.asyncio
async def test_health_success(client: EngineClient, test_endpoint: str, test_token: str, expected_user_agent: str):
    """Test successful health check."""
    with respx.mock() as mock:
        mock.get(f"{test_endpoint}/_health").mock(return_value=httpx.Response(200, json={"status": "ok"}))
        response = await client.health()
        assert response is True
        assert mock.called
        req = mock.calls.last.request
        assert req.headers["token"] == test_token
        assert req.headers["accept"] == "*/*"


@pytest.mark.asyncio
async def test_health_failure(client: EngineClient, test_endpoint: str):
    """Test failed health check."""
    with respx.mock() as mock:
        mock.get(f"{test_endpoint}/_health").mock(return_value=httpx.Response(500, json={"error": "internal server error"}))
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.health()
        assert exc_info.value.response.status_code == 500


@pytest.mark.asyncio
async def test_get_case_data_success(
    client: EngineClient, test_endpoint: str, test_token: str, request_id: int, expected_user_agent: str
):
    """Tests successful retrieval of case data."""
    expected_path = "/api/case_data"
    expected_url = f"{test_endpoint}{expected_path}"
    expected_response_payload = {"user": {"email": "toto"}}

    with respx.mock() as mock:
        mock.get(url__regex=rf".*{expected_path}.*").mock(
            return_value=httpx.Response(200, json=expected_response_payload)
        )
        response = await client.get_case_data(request_id, with_summary=False)

        assert response.model_dump(exclude_none=True, exclude_unset=True) == expected_response_payload
        assert mock.called
        req = mock.calls.last.request
        assert req.headers["token"] == test_token
        assert "request_id" in str(req.url)
        assert "with_summary=false" in str(req.url)


@pytest.mark.asyncio
async def test_get_case_data_failure(
    client: EngineClient, test_endpoint: str, test_token: str, request_id: int, expected_user_agent: str
):
    """Tests failure scenario for retrieving case data (e.g., 404 Not Found)."""
    expected_path = "/api/case_data"

    with respx.mock() as mock:
        mock.get(url__regex=rf".*{expected_path}.*").mock(return_value=httpx.Response(404))

        with pytest.raises(httpx.HTTPStatusError) as excinfo:
            await client.get_case_data(request_id)

        assert excinfo.value.response.status_code == 404
        assert mock.called


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

    with respx.mock() as mock:
        mock.post(f"{test_endpoint}/api/zieb/documents/ocr").mock(return_value=httpx.Response(200))
        result = await client.update_doc(doc_id, ocr_pages, pdf_url)
        assert result is True
        assert mock.called
        req = mock.calls.last.request
        assert req.headers["token"] == test_token
        assert json.loads(req.content) == expected_payload


@pytest.mark.asyncio
async def test_update_doc_failure(client: EngineClient, test_endpoint: str, doc_id: int):
    """Test failed document update."""
    with respx.mock() as mock:
        mock.post(f"{test_endpoint}/api/zieb/documents/ocr").mock(return_value=httpx.Response(400))
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.update_doc(doc_id, ["page text"])
        assert exc_info.value.response.status_code == 400


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
        attempt=2,
    )
    response_payload = {"status": "processed"}
    expected_url = f"{test_endpoint}/api/admin/action_triggers/{trigger_id}"

    with respx.mock() as mock:
        mock.put(url__regex=rf".*{trigger_id}.*").mock(return_value=httpx.Response(200, json=response_payload))
        updated_trigger = await client.action_trigger(trigger)

        assert updated_trigger is trigger
        assert updated_trigger.status == response_payload
        assert mock.called
        req = mock.calls.last.request
        assert req.headers["token"] == test_token
        assert "request_id" in str(req.url)
        assert "client=test_client" in str(req.url)


@pytest.mark.asyncio
async def test_action_trigger_failure(client: EngineClient, test_endpoint: str, trigger_id: str, request_id: int):
    """Test failed action trigger."""
    trigger = EngineTrigger(trigger_id=trigger_id, request_id=request_id)

    with respx.mock() as mock:
        mock.put(url__regex=rf".*{trigger_id}.*").mock(return_value=httpx.Response(404))
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.action_trigger(trigger)
        assert exc_info.value.response.status_code == 404


@pytest.mark.asyncio
async def test_create_request_success(client: EngineClient, test_endpoint: str, test_token: str, expected_user_agent: str):
    """Test successful request creation."""
    req = EngineRequest(
        product="prod_a",
        funnel="funnel_b",
        fields=[EngineField(field="field1", answer="value1", type=EngineTypeEnum.STRING)],
    )
    response_payload = {"request_id": 789, "status": "created"}
    expected_url = f"{test_endpoint}/api/admin/data_source"

    with respx.mock() as mock:
        mock.post(expected_url).mock(return_value=httpx.Response(201, json=response_payload))
        response = await client.create_request(req)
        assert response == response_payload
        assert len(mock.calls) > 0
        req_sent = mock.calls.last.request
        assert req_sent.headers["token"] == test_token
        assert req_sent.headers["content-type"].startswith("application/x-www-form-urlencoded")


@pytest.mark.asyncio
async def test_update_request_success(client: EngineClient, test_endpoint: str, test_token: str, request_id: int, expected_user_agent: str):
    """Test successful request update."""
    req = EngineRequest(
        product="prod_a_updated",
        funnel="funnel_b_updated",
        fields=[EngineField(field="field1", answer="value1_updated", type=EngineTypeEnum.STRING)],
    )
    response_payload = {"status": "updated"}
    expected_url = f"{test_endpoint}/api/admin/data_source"

    with respx.mock() as mock:
        mock.put(expected_url).mock(return_value=httpx.Response(200, json=response_payload))
        response = await client.update_request(request_id, req)
        assert response == response_payload
        assert mock.called
        req_sent = mock.calls.last.request
        assert req_sent.headers["token"] == test_token
        assert req_sent.headers["content-type"].startswith("application/x-www-form-urlencoded")


@pytest.mark.asyncio
async def test_update_insights_success(client: EngineClient, test_endpoint: str, test_token: str, expected_user_agent: str):
    """Test successful insights update."""
    docs_resp = DocsResponse(
        query=DocsQuery(limit=100, mode=WithContentMode.SUMMARY, vectordb=ManagerEnum.NONE, output=OutputFormatEnum.JSON),
        docs=[Content(metadata={"doc_id": "doc1"}, full="content1")],
    )
    response_payload = {"message": "Insights updated"}
    expected_url = f"{test_endpoint}/api/insights"

    with respx.mock() as mock:
        mock.post(expected_url).mock(return_value=httpx.Response(200, json=response_payload))
        response = await client.update_insights(docs_resp)
        assert response == response_payload
        assert mock.called
        req_sent = mock.calls.last.request
        assert req_sent.headers["token"] == test_token
        assert req_sent.headers["content-type"] == "application/json"
        body = json.loads(req_sent.content)
        assert "query" in body
        assert "docs" in body


@pytest.mark.asyncio
async def test_update_doc_suggestions_aws_success(client: EngineClient, test_endpoint: str, test_token: str, expected_user_agent: str):
    """Test successful document suggestions update using AwsClassifierResult."""
    aws_result = AwsClassifierResult(
        job=AwsJobDescribe(id="job-123", name="test-job", submit_time=datetime.now(), end_time=datetime.now()),
        inference=[AwsInference(line="doc1", classes=[])],
        model="aws-model-v1",
    )
    response_payload = {"message": "Suggestions updated via AWS"}
    expected_url = f"{test_endpoint}/api/zieb/documents/update_suggestions"

    with respx.mock() as mock:
        mock.post(expected_url).mock(return_value=httpx.Response(200, json=response_payload))
        response = await client.update_doc_suggestions(aws_result)
        assert response == response_payload
        assert mock.called
        req_sent = mock.calls.last.request
        assert req_sent.headers["token"] == test_token


@pytest.mark.asyncio
async def test_update_doc_suggestions_agent_success(client: EngineClient, test_endpoint: str, test_token: str, expected_user_agent: str):
    """Test successful document suggestions update using AgentClassifierWorkflowOutput."""
    agent_result = AgentClassifierWorkflowOutput(
        result=ClassificationRentalResponse(
            classification=ClassificationRentalScore(category="cat1", reasoning="reason1", confidence_score=0.9)
        )
    )
    response_payload = {"message": "Suggestions updated via Agent"}
    expected_url = f"{test_endpoint}/api/zieb/documents/update_suggestions"

    with respx.mock() as mock:
        mock.post(expected_url).mock(return_value=httpx.Response(200, json=response_payload))
        response = await client.update_doc_suggestions(agent_result)
        assert response == response_payload
        assert mock.called
        req_sent = mock.calls.last.request
        assert req_sent.headers["token"] == test_token


@pytest.mark.asyncio
async def test_update_doc_suggestions_failure(client: EngineClient, test_endpoint: str):
    """Test failed document suggestions update."""
    agent_result = AgentClassifierWorkflowOutput(
        result=ClassificationRentalResponse(
            classification=ClassificationRentalScore(category="cat1", reasoning="reason1", confidence_score=0.9)
        )
    )
    expected_url = f"{test_endpoint}/api/zieb/documents/update_suggestions"

    with respx.mock() as mock:
        mock.post(expected_url).mock(return_value=httpx.Response(400, json={"error": "bad input"}))
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.update_doc_suggestions(agent_result)
        assert exc_info.value.response.status_code == 400


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


@pytest.mark.asyncio
async def test_scheduled_call_response_success(client: EngineClient, test_endpoint: str, test_token: str, expected_user_agent: str):
    """Test successful scheduled call response."""
    mock_event = MagicMock(spec=TelliWebhook)
    mock_event.model_dump_json.return_value = '{"event": "call_answered", "call_sid": "C123"}'

    expected_payload = {"event": "call_answered", "call_sid": "C123"}
    response_payload = {"status": "ok"}
    expected_url = f"{test_endpoint}/api/scheduled_call_response"

    with respx.mock() as mock:
        mock.post(expected_url).mock(return_value=httpx.Response(200, json=response_payload))
        response = await client.scheduled_call_response(mock_event)

        assert response == response_payload
        mock_event.model_dump_json.assert_called_once_with(exclude_none=True, exclude_unset=True)
        assert mock.called
        req_sent = mock.calls.last.request
        assert req_sent.headers["token"] == test_token
        assert json.loads(req_sent.content) == expected_payload


@pytest.mark.asyncio
async def test_scheduled_call_response_failure(client: EngineClient, test_endpoint: str):
    """Test failed scheduled call response."""
    mock_event = MagicMock(spec=TelliWebhook)
    mock_event.model_dump_json.return_value = '{"event": "call_failed"}'
    expected_url = f"{test_endpoint}/api/scheduled_call_response"

    with respx.mock() as mock:
        mock.post(expected_url).mock(return_value=httpx.Response(400))
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.scheduled_call_response(mock_event)
        assert exc_info.value.response.status_code == 400


@pytest.mark.asyncio
async def test_get_request_documents_success(
    client: EngineClient, test_endpoint: str, test_token: str, request_id: int, expected_user_agent: str
):
    """Test successful retrieval of request documents."""
    expected_path = f"/api/admin/requests/{request_id}/documents.json"
    expected_url = f"{test_endpoint}{expected_path}"
    response_payload: dict = {
        "request": {
            "id": request_id,
            "files": [
                {
                    "id": 2469711,
                    "physical_mails": [],
                    "type": "IN_Erfolgs_Vereinbarung bei Mietsenkung_en",
                    "image": False,
                    "pdf": True,
                    "filename": "Erfolgs-Vereinbarung bei Mietsenkung_English.pdf",
                    "incoming": False,
                    "uncategorized": False,
                    "edit_url": f"/admin/requests/{request_id}/zieb?document_id=2469711",
                    "approved": True,
                    "attachment": False,
                    "created_at": "2025-11-26T15:01:36.778Z",
                    "court_processing_kind": None,
                    "type_title": "IN_Erfolgs_Vereinbarung bei Mietsenkung_en",
                    "approved_at": "Mittwoch, 26. November 2025, 16:01 Uhr",
                    "uploaded_by": "00 Mietright Zentrale",
                    "approved_by": "00 Mietright Zentrale",
                    "created_at_text": "etwa 20 Stunden",
                    "approved_at_text": "Mittwoch, 26. November 2025, 16:01 Uhr",
                    "sensitive": False,
                    "eb_date": None,
                    "court_id": None,
                    "court_type": False,
                    "file_extension": "pdf",
                    "court_attachment": False,
                    "original_size": 78920,
                    "size": "77,1 KB",
                }
            ],
        },
        "presigned_post": {
            "s3-data": {
                "key": f"requests/{request_id}/files/some-uuid/${{filename}}",
                "success_action_status": "201",
                "acl": "private",
                "policy": "some-policy",
                "x-amz-credential": "some-credential",
                "x-amz-algorithm": "AWS4-HMAC-SHA256",
                "x-amz-date": "20251127T112143Z",
                "x-amz-signature": "some-signature",
            },
            "s3-url": "https://some.s3.url.com",
            "s3-host": "some.s3.host.com",
        },
    }

    with respx.mock() as mock:
        mock.get(expected_url).mock(return_value=httpx.Response(200, json=response_payload))
        response = await client.get_request_documents(request_id)
        assert isinstance(response, RequestDocumentsResponse)
        assert response.request.id == request_id
        assert len(response.request.files) == 1
        assert response.request.files[0].id == 2469711
        assert response.presigned_post.s3_url == "https://some.s3.url.com"
        assert mock.called
        req_sent = mock.calls.last.request
        assert req_sent.headers["token"] == test_token


@pytest.mark.asyncio
async def test_get_request_documents_failure(client: EngineClient, test_endpoint: str, request_id: int):
    """Test failed retrieval of request documents."""
    expected_url = f"{test_endpoint}/api/admin/requests/{request_id}/documents.json"
    with respx.mock() as mock:
        mock.get(expected_url).mock(return_value=httpx.Response(404))
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.get_request_documents(request_id)
        assert exc_info.value.response.status_code == 404


@pytest.mark.asyncio
async def test_get_document_json_success(
    client: EngineClient, test_endpoint: str, test_token: str, doc_id: int, expected_user_agent: str
):
    """Test successfully retrieving a document URL as JSON."""
    expected_path = f"/api/admin/documents/{doc_id}"
    expected_url = f"{test_endpoint}{expected_path}"
    presigned_url = "https://s3.example.com/some/file.pdf?sig=123"
    response_payload = {"url": presigned_url}

    with respx.mock() as mock:
        mock.get(expected_url).mock(return_value=httpx.Response(200, json=response_payload))
        response = await client.get_document_url(doc_id)
        assert isinstance(response, DocumentUrlResponse)
        assert response.url == presigned_url
        assert mock.called
        req_sent = mock.calls.last.request
        assert req_sent.headers["token"] == test_token
        assert req_sent.headers["accept"] == "application/json"


@pytest.mark.asyncio
async def test_download_document_spooled_success(
    client: EngineClient, test_endpoint: str, test_token: str, doc_id: int, expected_user_agent: str
):
    """Test successfully downloading a document file to a SpooledTemporaryFile."""
    api_path = f"/api/admin/documents/{doc_id}"
    api_url = f"{test_endpoint}{api_path}"
    s3_url = "https://s3.example.com/some/file.pdf?sig=123"
    file_content = b"This is a test PDF content."

    with respx.mock() as mock:
        # httpx follows redirects at client level; mock the final URL directly
        mock.get(api_url).mock(return_value=httpx.Response(200, content=file_content))

        response_file = await client.download_document(doc_id)

        assert response_file.read() == file_content
        response_file.close()
        assert mock.called
        req_sent = mock.calls.last.request
        assert req_sent.headers["token"] == test_token


@pytest.mark.asyncio
async def test_download_document_to_directory_success(
    client: EngineClient, test_endpoint: str, doc_id: int, tmp_path: os.PathLike
):
    """Test successfully downloading a document to a directory, inferring filename."""
    api_path = f"/api/admin/documents/{doc_id}"
    api_url = f"{test_endpoint}{api_path}"
    file_content = b"This is content for a directory download."
    filename = "inferred_document.pdf"

    with respx.mock() as mock:
        mock.get(api_url).mock(
            return_value=httpx.Response(
                200,
                content=file_content,
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        )

        returned_path = await client.download_document(doc_id, filepath=str(tmp_path))

        expected_output_path = os.path.join(tmp_path, filename)
        assert returned_path == expected_output_path
        assert os.path.exists(expected_output_path)
        with open(expected_output_path, "rb") as f:
            assert f.read() == file_content


@pytest.mark.asyncio
async def test_download_document_to_file_success(
    client: EngineClient, test_endpoint: str, doc_id: int, tmp_path: os.PathLike
):
    """Test successfully downloading a document to a specified file path."""
    api_path = f"/api/admin/documents/{doc_id}"
    api_url = f"{test_endpoint}{api_path}"
    file_content = b"This is file content saved to disk."
    output_path = os.path.join(tmp_path, "downloaded.pdf")

    with respx.mock() as mock:
        mock.get(api_url).mock(return_value=httpx.Response(200, content=file_content))

        result = await client.download_document(doc_id, filepath=output_path)

        assert result is None
        assert os.path.exists(output_path)
        with open(output_path, "rb") as f:
            assert f.read() == file_content


# TODO: Add tests verifying specific header content (e.g., token, content-type) more explicitly if needed.
# TODO: Add tests for edge cases (e.g., empty lists, optional parameters).
