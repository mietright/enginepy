import datetime
from unittest.mock import AsyncMock

import pytest

# Import functions/models to test
from enginepy.agents.case_summary.functions import (
    get_collection_summary,
    system_instruction,
)
from enginepy.agents.case_summary.models import ConnyRequestSummary, ConnyRequestSummaryCtx
from enginepy.gen.antbed import Content, DocsQuery, DocsResponse
from enginepy.models import Docs as EnginepyDocsModel  # Alias to avoid name clash

# --- Test Data ---
REQ_ID = 123
COLLECTION_NAME = f"conny-request:{REQ_ID}"
DATE_STR_NOW = datetime.datetime.now(datetime.UTC).isoformat()
DATE_STR_PAST = datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC).isoformat()
DATE_OBJ_PAST = datetime.datetime.fromisoformat(DATE_STR_PAST)

@pytest.fixture
def sample_ctx() -> ConnyRequestSummaryCtx:
    """Provides a basic ConnyRequestSummaryCtx."""
    req = ConnyRequestSummary(request_id=REQ_ID, limit=10)
    return ConnyRequestSummaryCtx.from_summary(req)

@pytest.fixture
def sample_ctx_with_date() -> ConnyRequestSummaryCtx:
    """Provides a ConnyRequestSummaryCtx with a last_document_date."""
    req = ConnyRequestSummary(request_id=REQ_ID, limit=10)
    ctx = ConnyRequestSummaryCtx.from_summary(req)
    ctx.last_document_date = DATE_STR_PAST
    ctx.last_document_id = "doc-past"
    return ctx

@pytest.fixture
def mock_antbed_client(mocker) -> AsyncMock:
    """Mocks the antbed_client and its scroll method."""
    mock_client = AsyncMock()
    mock_client.scroll = AsyncMock()
    mocker.patch('enginepy.agents.case_summary.functions.antbed_client', return_value=mock_client)
    return mock_client

# --- Tests ---

def test_system_instruction():
    """Test that system_instruction returns a non-empty string."""
    instruction = system_instruction()
    assert isinstance(instruction, str)
    assert len(instruction) > 0
    assert "legal consultant" in instruction  # Basic check

@pytest.mark.asyncio
async def test_get_collection_summary_no_docs(sample_ctx, mock_antbed_client):
    """Test get_collection_summary when no documents are returned."""
    # Mock antbed scroll to return empty DocsResponse inside Docs
    mock_response = EnginepyDocsModel(docs=DocsResponse(docs=[], query=DocsQuery()))
    mock_antbed_client.scroll.return_value = mock_response

    result = await get_collection_summary(sample_ctx)

    # Assertions
    mock_antbed_client.scroll.assert_called_once()
    call_args, _ = mock_antbed_client.scroll.call_args
    sent_req: DocsQuery = call_args[0]
    assert isinstance(sent_req, DocsQuery)
    assert sent_req.collection_name == COLLECTION_NAME
    assert sent_req.limit == sample_ctx.limit
    assert sent_req.date_gt is None  # No date in sample_ctx
    assert sent_req.mode == sample_ctx.mode
    assert sent_req.output == sample_ctx.output

    assert sample_ctx.retrieved_all is True  # Should be set to True
    assert result == ""  # content_str() of empty docs is ""

@pytest.mark.asyncio
async def test_get_collection_summary_with_docs_new(sample_ctx, mock_antbed_client):
    """Test get_collection_summary with new documents."""
    doc1_meta = {"id": "doc-new-1", "date": DATE_STR_NOW, "name": "file1.txt"}
    doc2_meta = {"id": "doc-new-2", "date": DATE_STR_NOW, "name": "file2.txt"}
    docs_list = [
        Content(metadata=doc1_meta, summary="Summary 1"),
        Content(metadata=doc2_meta, summary="Summary 2"),
    ]
    mock_response_obj = DocsResponse(docs=docs_list, query=DocsQuery())
    mock_response = EnginepyDocsModel(docs=mock_response_obj)
    mock_antbed_client.scroll.return_value = mock_response
    expected_json_str = mock_response_obj.model_dump_json(exclude_none=True, exclude_unset=True, exclude_defaults=True, indent=2)

    result = await get_collection_summary(sample_ctx)

    # Assertions
    mock_antbed_client.scroll.assert_called_once()
    assert sample_ctx.retrieved_all is False  # Should remain False
    # Check context updated with last doc info
    assert sample_ctx.last_document_id == doc2_meta["id"]
    assert sample_ctx.last_document_date == doc2_meta["date"]
    assert result == expected_json_str

@pytest.mark.asyncio
async def test_get_collection_summary_with_docs_same_last_id(sample_ctx_with_date, mock_antbed_client):
    """Test get_collection_summary when the last returned doc ID matches context."""
    # Use sample_ctx_with_date which has last_document_id = "doc-past"
    doc1_meta = {"id": "doc-new-1", "date": DATE_STR_NOW, "name": "file1.txt"}
    doc2_meta = {"id": sample_ctx_with_date.last_document_id, "date": DATE_STR_NOW, "name": "file2.txt"}  # Match ID
    docs_list = [
        Content(metadata=doc1_meta, summary="Summary 1"),
        Content(metadata=doc2_meta, summary="Summary 2"),
    ]
    mock_response_obj = DocsResponse(docs=docs_list, query=DocsQuery())
    mock_response = EnginepyDocsModel(docs=mock_response_obj)
    mock_antbed_client.scroll.return_value = mock_response
    expected_json_str = mock_response_obj.model_dump_json(exclude_none=True, exclude_unset=True, exclude_defaults=True, indent=2)

    result = await get_collection_summary(sample_ctx_with_date)

    # Assertions
    mock_antbed_client.scroll.assert_called_once()
    call_args, _ = mock_antbed_client.scroll.call_args
    sent_req: DocsQuery = call_args[0]
    assert sent_req.date_gt == DATE_OBJ_PAST  # Check date_gt was set

    assert sample_ctx_with_date.retrieved_all is True  # Should be set True because last ID matched
    # Context date/id should NOT be updated beyond the initial state if ID matches
    assert sample_ctx_with_date.last_document_id == "doc-past"
    assert sample_ctx_with_date.last_document_date == DATE_STR_NOW  # Updated to new date
    assert result == expected_json_str

