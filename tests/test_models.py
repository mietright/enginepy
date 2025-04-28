import pytest
from pydantic import BaseModel, ValidationError

# Import dependent models from other modules
from enginepy.agents.case_summary.models import ConnyRequestSummary, SummaryResponse
from enginepy.agents.rental_classifier.models import (
    ClassificationRentalCtx,
    ClassificationRentalResponse,
    ClassificationRentalType,
)
from enginepy.gen.antbed import Content, DocsResponse, OutputFormatEnum, WithContentMode

# Import models from enginepy.models
from enginepy.models import (
    AgentCaseSummaryWorkflowInput,
    AgentCaseSummaryWorkflowOutput,
    AgentClassifierWorkflowInput,
    AgentClassifierWorkflowOutput,
    AgentRunCost,
    AgentWorkflowInput,
    AgentWorkflowOutput,
    AnyData,
    AsyncResponse,
    Docs,
    WorkflowInfo,
)

# --- Test Data ---

VALID_WORKFLOW_INFO_DICT = {"name": "test-workflow", "wid": "wf-123"}
VALID_AGENT_RUN_COST_DICT = {"total_tokens": 150, "total_time": 10.5, "total_cost": 0.01}

VALID_CONNY_REQUEST_SUMMARY_DICT = {
    "query": "test query",
    "request_id": 123, # Change to integer type
    "max_docs": 10,
    "max_words_per_chunk": 500,
    "max_chunks_per_doc": 5,
    "max_total_chunks": 20,
    "model_name": "gpt-4",
}
VALID_CONNY_REQUEST_SUMMARY = ConnyRequestSummary(**VALID_CONNY_REQUEST_SUMMARY_DICT)


VALID_SUMMARY_RESPONSE_LIST = [
SummaryResponse(summary="Summary part 1", timeline="Timeline 1",
                summary_changes=[], timeline_changes=[],
                last_document_id="doc-1", last_document_date="2024-01-15T10:30:00Z",
                ),
SummaryResponse(summary="Summary part 2",
                timeline="Timeline 2",
                summary_changes=[], timeline_changes=[],
                last_document_id="doc-2", last_document_date="2024-01-15T11:30:00Z",
                )
]

VALID_CLASSIFICATION_RENTAL_CTX_DICT = {
    "user_id": "user-789",
    "collection_id": "col-xyz",
    "model_name": "gemini-pro",
}
VALID_CLASSIFICATION_RENTAL_CTX = ClassificationRentalCtx(**VALID_CLASSIFICATION_RENTAL_CTX_DICT)


VALID_CLASSIFICATION_RENTAL_RESPONSE_DICT = {
    "classification": {
        "reasoning": "The document is a rental contract based on the content and structure.",
        "category": ClassificationRentalType.RENTAL_CONTRACT,
        "confidence_score": 0.9
    },
    "next_categories": [
        {
            "reasoning": "The document contains a rental increase letter, which is a common type of rental document.",
            "category": ClassificationRentalType.RENT_INCREASE_LETTER,
            "confidence_score": 0.05
        },
        {
            "reasoning": "The document is a rental contract but is unsigned, indicating it may not be valid.",
            "category": ClassificationRentalType.GENERAL_CUSTOMER,
            "confidence_score": 0.03
        }
    ]
}
VALID_CLASSIFICATION_RENTAL_RESPONSE = ClassificationRentalResponse(**VALID_CLASSIFICATION_RENTAL_RESPONSE_DICT)

VALID_DOCS_QUERY_DICT = {
    "limit": 10,
    "mode": WithContentMode.SUMMARY,
    "output": OutputFormatEnum.JSON,
}

VALID_DOCS_RESPONSE_DICT = {
    "docs": [
        Content(metadata={"source": "file1.txt"}, summary="Doc 1 summary"),
        Content(metadata={"source": "file2.pdf"}, summary="Doc 2 summary"),
    ],
    "query": VALID_DOCS_QUERY_DICT,
}
VALID_DOCS_RESPONSE_OBJ = DocsResponse(**VALID_DOCS_RESPONSE_DICT)
VALID_DOCS_RESPONSE_JSON = VALID_DOCS_RESPONSE_OBJ.model_dump_json(exclude_none=True, exclude_unset=True, exclude_defaults=True, indent=2)


# --- Test Functions ---

def test_async_response_secret_key():
    """Test the secret_key property of AsyncResponse."""
    ar = AsyncResponse(job_id="any_job_id", status="PENDING")
    expected_key = b"NhqPtmfle3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j-antgent"
    assert ar.secret_key == expected_key


def test_docs_model():
    """Test the Docs model instantiation and methods."""
    # Test defaults
    docs_default = Docs()
    assert docs_default.markdown is None
    assert docs_default.docs is None
    assert docs_default.output == OutputFormatEnum.JSON
    assert docs_default.mode == WithContentMode.SUMMARY
    assert docs_default.content() is None
    assert docs_default.content_str() == ""

    # Test with markdown string and output != JSON
    markdown_content = "Simple markdown content"
    docs_md = Docs(markdown=markdown_content, output=OutputFormatEnum.MARKDOWN)
    assert docs_md.markdown == markdown_content
    assert docs_md.docs is None
    assert docs_md.output == OutputFormatEnum.MARKDOWN
    assert docs_md.content() == markdown_content
    assert docs_md.content_str() == markdown_content

    # Test with None markdown and output != JSON
    docs_none_md = Docs(markdown=None, output=OutputFormatEnum.MARKDOWN)
    assert docs_none_md.markdown is None
    assert docs_none_md.content() is None
    assert docs_none_md.content_str() == ""

    # Test with DocsResponse object and output=JSON (default)
    docs_json = Docs(docs=VALID_DOCS_RESPONSE_OBJ) # output defaults to JSON
    assert docs_json.markdown is None
    assert docs_json.docs == VALID_DOCS_RESPONSE_OBJ
    assert docs_json.output == OutputFormatEnum.JSON
    content = docs_json.content()
    assert isinstance(content, DocsResponse)
    assert content == VALID_DOCS_RESPONSE_OBJ
    assert docs_json.content_str() == VALID_DOCS_RESPONSE_JSON

    # Test with DocsResponse object and output != JSON (should return markdown)
    docs_json_output_md = Docs(docs=VALID_DOCS_RESPONSE_OBJ, markdown="Fallback", output=OutputFormatEnum.MARKDOWN)
    assert docs_json_output_md.markdown == "Fallback"
    assert docs_json_output_md.docs == VALID_DOCS_RESPONSE_OBJ
    assert docs_json_output_md.output == OutputFormatEnum.MARKDOWN
    assert docs_json_output_md.content() == "Fallback"
    assert docs_json_output_md.content_str() == "Fallback"

    # Test with empty docs list in DocsResponse
    empty_docs_response = DocsResponse(docs=[], query=VALID_DOCS_QUERY_DICT)
    docs_empty = Docs(docs=empty_docs_response)
    assert docs_empty.content_str() == ""


def test_any_data_model():
    """Test the AnyData model allows extra fields."""
    data_dict = {"key": "value", "number": 1, "extra_field": True}
    model = AnyData(**data_dict)
    assert model.model_dump() == data_dict # Check if extra field is preserved

    # Test with other types (though less common use case for extra='allow')
    AnyData(data_list=[1, 2]) # This won't work as expected with extra='allow' on root
    # The primary use of extra='allow' is for dict-like structures


def test_agent_workflow_input_generic():
    """Test the generic AgentWorkflowInput model."""
    class SampleContext(BaseModel):
        field1: str
        field2: int

    context_data = SampleContext(field1="test", field2=123)
    input_str = "process this"

    # Test instantiation
    inp = AgentWorkflowInput[SampleContext](context=context_data, input=input_str)
    assert inp.context == context_data
    assert inp.input == input_str

    # Test default input string
    inp_default_input = AgentWorkflowInput[SampleContext](context=context_data)
    assert inp_default_input.context == context_data
    assert inp_default_input.input == ""

    # Test missing context
    with pytest.raises(ValidationError):
        AgentWorkflowInput[SampleContext](input=input_str)


def test_agent_run_cost_model():
    """Test the AgentRunCost model."""
    # Test instantiation with values
    cost = AgentRunCost(**VALID_AGENT_RUN_COST_DICT)
    assert cost.total_tokens == VALID_AGENT_RUN_COST_DICT["total_tokens"]
    assert cost.total_time == VALID_AGENT_RUN_COST_DICT["total_time"]
    assert cost.total_cost == VALID_AGENT_RUN_COST_DICT["total_cost"]

    # Test default values
    cost_default = AgentRunCost()
    assert cost_default.total_tokens == 0
    assert cost_default.total_time == 0.0
    assert cost_default.total_cost == 0.0


def test_workflow_info_model():
    """Test the WorkflowInfo model."""
    # Test instantiation with values
    info = WorkflowInfo(**VALID_WORKFLOW_INFO_DICT)
    assert info.name == VALID_WORKFLOW_INFO_DICT["name"]
    assert info.wid == VALID_WORKFLOW_INFO_DICT["wid"]

    # Test default values
    info_default = WorkflowInfo()
    assert info_default.name == ""
    assert info_default.wid == ""


def test_agent_workflow_output_generic():
    """Test the generic AgentWorkflowOutput model."""
    class SampleResult(BaseModel):
        result_field: bool

    result_data = SampleResult(result_field=True)
    cost_data = AgentRunCost(**VALID_AGENT_RUN_COST_DICT)
    wf_info_data = WorkflowInfo(**VALID_WORKFLOW_INFO_DICT)
    metadata_data = {"run_by": "tester"}

    # Test full instantiation
    out = AgentWorkflowOutput[SampleResult](
        result=result_data,
        metadata=metadata_data,
        cost=cost_data,
        workflow_info=wf_info_data,
        extra_field="allowed" # Test extra='allow'
    )
    assert out.result == result_data
    assert out.metadata == metadata_data
    assert out.cost == cost_data
    assert out.workflow_info == wf_info_data
    assert out.model_extra is not None
    assert out.model_extra.get("extra_field") == "allowed"

    # Test minimal instantiation (only required 'result')
    out_minimal = AgentWorkflowOutput[SampleResult](result=result_data)
    assert out_minimal.result == result_data
    assert out_minimal.metadata == {} # Default factory
    assert out_minimal.cost is None # Default
    assert out_minimal.workflow_info is None # Default
    assert out_minimal.model_extra == {}

    # Test missing result
    with pytest.raises(ValidationError):
        AgentWorkflowOutput[SampleResult](cost=cost_data)


def test_agent_summary_workflow_input():
    """Test AgentCaseSummaryWorkflowInput model."""
    inp = AgentCaseSummaryWorkflowInput(
        context=VALID_CONNY_REQUEST_SUMMARY,
        input="optional input string",
    )
    assert isinstance(inp, AgentWorkflowInput) # Check inheritance
    assert inp.context == VALID_CONNY_REQUEST_SUMMARY
    assert inp.input == "optional input string"

    # Test missing context
    with pytest.raises(ValidationError):
        AgentCaseSummaryWorkflowInput(input="some string")


def test_agent_summary_workflow_output():
    """Test AgentCaseSummaryWorkflowOutput model."""
    cost = AgentRunCost(**VALID_AGENT_RUN_COST_DICT)
    wf_info = WorkflowInfo(**VALID_WORKFLOW_INFO_DICT)

    out = AgentCaseSummaryWorkflowOutput(
        result=VALID_SUMMARY_RESPONSE_LIST,
        cost=cost,
        workflow_info=wf_info,
    )
    assert isinstance(out, AgentWorkflowOutput) # Check inheritance
    assert out.result == VALID_SUMMARY_RESPONSE_LIST
    assert out.cost == cost
    assert out.workflow_info == wf_info

    # Test minimal (only result)
    out_minimal = AgentCaseSummaryWorkflowOutput(result=VALID_SUMMARY_RESPONSE_LIST)
    assert out_minimal.result == VALID_SUMMARY_RESPONSE_LIST
    assert out_minimal.cost is None
    assert out_minimal.workflow_info is None

    # Test missing result
    with pytest.raises(ValidationError):
         AgentCaseSummaryWorkflowOutput(cost=cost)


def test_agent_classifier_workflow_input():
    """Test AgentClassifierWorkflowInput model."""
    inp = AgentClassifierWorkflowInput(
        context=VALID_CLASSIFICATION_RENTAL_CTX,
        input="classify this text",
    )
    assert isinstance(inp, AgentWorkflowInput) # Check inheritance
    assert inp.context == VALID_CLASSIFICATION_RENTAL_CTX
    assert inp.input == "classify this text"

    # Test missing context
    with pytest.raises(ValidationError):
        AgentClassifierWorkflowInput(input="some text")


def test_agent_classifier_workflow_output():
    """Test AgentClassifierWorkflowOutput model."""
    cost = AgentRunCost(**VALID_AGENT_RUN_COST_DICT)
    wf_info = WorkflowInfo(**VALID_WORKFLOW_INFO_DICT)

    out = AgentClassifierWorkflowOutput(
        result=VALID_CLASSIFICATION_RENTAL_RESPONSE,
        cost=cost,
        workflow_info=wf_info,
    )
    assert isinstance(out, AgentWorkflowOutput) # Check inheritance
    assert out.result == VALID_CLASSIFICATION_RENTAL_RESPONSE
    assert out.cost == cost
    assert out.workflow_info == wf_info

    # Test minimal (only result)
    out_minimal = AgentClassifierWorkflowOutput(result=VALID_CLASSIFICATION_RENTAL_RESPONSE)
    assert out_minimal.result == VALID_CLASSIFICATION_RENTAL_RESPONSE
    assert out_minimal.cost is None
    assert out_minimal.workflow_info is None

    # Test missing result
    with pytest.raises(ValidationError):
         AgentClassifierWorkflowOutput(cost=cost)
