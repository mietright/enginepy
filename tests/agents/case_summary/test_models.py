from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

# Import models to test
from enginepy.agents.case_summary.models import (
    ConnyRequestSummary,
    ConnyRequestSummaryCtx,
    SummaryMergerResponse,
    SummaryResponse,
    TimelineMergerResponse,
)
from enginepy.gen.antbed import OutputFormatEnum, WithContentMode

# --- Test Data ---
DATE_STR = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC).isoformat()
PREVIOUS_SUMMARY_RESP = SummaryResponse(
    summary="Previous summary content.",
    timeline="Previous timeline content.",
    last_document_id="doc-prev",
    last_document_date=DATE_STR,
    summary_changes=["prev_change1", "prev_change2"],
    timeline_changes=["prev_changeA", "prev_changeB"],
)
CONNY_REQ_DICT = {
    "request_id": 12345,
    "limit": 20,
}
CONNY_REQ_WITH_PREVIOUS_DICT = {
    "request_id": 54321,
    "limit": 10,
    "previous": PREVIOUS_SUMMARY_RESP.model_dump(),
}

# --- Tests ---

def test_summary_response_with_values():
    """Test SummaryResponse instantiation with values."""
    data = {
        "summary": "Test Summary",
        "timeline": "Test Timeline",
        "summary_changes": ["change1"],
        "timeline_changes": ["changeA"],
        "last_document_id": "doc-1",
        "last_document_date": DATE_STR,
    }
    resp = SummaryResponse(**data)
    assert resp.summary == data["summary"]
    assert resp.timeline == data["timeline"]
    assert resp.summary_changes == data["summary_changes"]
    assert resp.timeline_changes == data["timeline_changes"]
    assert resp.last_document_id == data["last_document_id"]
    assert resp.last_document_date == data["last_document_date"]
    # Ensure date is stored as string
    assert isinstance(resp.last_document_date, str)

def test_conny_request_summary_required():
    """Test ConnyRequestSummary required fields."""
    req = ConnyRequestSummary(**CONNY_REQ_DICT)
    assert req.request_id == CONNY_REQ_DICT["request_id"]
    assert req.limit == CONNY_REQ_DICT["limit"]
    assert req.previous is None

    with pytest.raises(ValidationError):
        ConnyRequestSummary(limit=10) # Missing request_id

def test_conny_request_summary_with_previous():
    """Test ConnyRequestSummary with a previous SummaryResponse."""
    req = ConnyRequestSummary(**CONNY_REQ_WITH_PREVIOUS_DICT)
    assert req.request_id == CONNY_REQ_WITH_PREVIOUS_DICT["request_id"]
    assert req.previous is not None
    assert isinstance(req.previous, SummaryResponse)
    assert req.previous.summary == PREVIOUS_SUMMARY_RESP.summary
    assert req.previous.last_document_id == PREVIOUS_SUMMARY_RESP.last_document_id

def test_conny_request_summary_ctx_defaults():
    """Test ConnyRequestSummaryCtx default values."""
    # Need a base ConnyRequestSummary first
    base_req = ConnyRequestSummary(**CONNY_REQ_DICT)
    ctx = ConnyRequestSummaryCtx.model_validate(base_req.model_dump())

    assert ctx.request_id == base_req.request_id
    assert ctx.limit == base_req.limit
    assert ctx.previous is None
    assert ctx.retrieved_all is False
    assert ctx.mode == WithContentMode.SUMMARY
    assert ctx.output == OutputFormatEnum.JSON
    assert ctx.last_document_id == ""
    assert ctx.last_document_date == ""

def test_conny_request_summary_ctx_from_summary_no_previous():
    """Test ConnyRequestSummaryCtx.from_summary without previous data."""
    base_req = ConnyRequestSummary(**CONNY_REQ_DICT)
    ctx = ConnyRequestSummaryCtx.from_summary(base_req)

    assert ctx.request_id == base_req.request_id
    assert ctx.limit == base_req.limit
    assert ctx.previous is None
    assert ctx.retrieved_all is False # Explicitly set by from_summary
    assert ctx.mode == WithContentMode.SUMMARY # Default
    assert ctx.output == OutputFormatEnum.JSON # Default
    assert ctx.last_document_id == "" # From previous (None)
    assert ctx.last_document_date == "" # From previous (None)

def test_conny_request_summary_ctx_from_summary_with_previous():
    """Test ConnyRequestSummaryCtx.from_summary with previous data."""
    base_req = ConnyRequestSummary(**CONNY_REQ_WITH_PREVIOUS_DICT)
    ctx = ConnyRequestSummaryCtx.from_summary(base_req)

    assert ctx.request_id == base_req.request_id
    assert ctx.limit == base_req.limit
    assert ctx.previous == base_req.previous # Copied over
    assert ctx.retrieved_all is False # Explicitly set by from_summary
    assert ctx.mode == WithContentMode.SUMMARY # Default
    assert ctx.output == OutputFormatEnum.JSON # Default
    # Values copied from previous
    assert ctx.last_document_id == PREVIOUS_SUMMARY_RESP.last_document_id
    assert ctx.last_document_date == PREVIOUS_SUMMARY_RESP.last_document_date
    assert isinstance(ctx.last_document_date, str) # Ensure it remains string

def test_timeline_merger_response():
    """Test TimelineMergerResponse."""
    data = {"timeline": "Merged Timeline", "changes": ["changeA", "changeB"]}
    resp = TimelineMergerResponse(**data)
    assert resp.timeline == data["timeline"]
    assert resp.changes == data["changes"]

    # Test defaults
    resp_default = TimelineMergerResponse(timeline="Only Timeline", changes=[])
    assert resp_default.timeline == "Only Timeline"
    assert resp_default.changes == []

    # Test missing required field
    with pytest.raises(ValidationError):
        TimelineMergerResponse(changes=["changeA"]) # Missing timeline

def test_summary_merger_response():
    """Test SummaryMergerResponse."""
    data = {"summary": "Merged Summary", "changes": ["change1", "change2"]}
    resp = SummaryMergerResponse(**data)
    assert resp.summary == data["summary"]
    assert resp.changes == data["changes"]

    # Test defaults
    resp_default = SummaryMergerResponse(summary="Only Summary", changes=[])
    assert resp_default.summary == "Only Summary"
    assert resp_default.changes == []

    # Test missing required field
    with pytest.raises(ValidationError):
        SummaryMergerResponse(changes=["change1"]) # Missing summary
