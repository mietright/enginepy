from unittest.mock import AsyncMock, MagicMock

import pytest
from google.genai import types as genai_types  # Use alias to avoid conflict

# Import classes/models to test
from enginepy.agents.rental_classifier.gemini import ClassifierRentalGeminiAgent
from enginepy.agents.rental_classifier.models import (
    ClassificationRentalCtx,
    ClassificationRentalResponse,
    ClassificationRentalScore,
    ClassificationRentalType,
)

# --- Test Data ---
DOC_ID = 555
REQ_ID = 444
INPUT_TEXT = "Document text for Gemini classification."
CUSTOM_MODEL = "gemini-custom-model-xyz"

@pytest.fixture
def sample_ctx() -> ClassificationRentalCtx:
    """Provides a basic ClassificationRentalCtx."""
    return ClassificationRentalCtx(request_id=REQ_ID, document_id=DOC_ID)

@pytest.fixture
def sample_classification_response() -> ClassificationRentalResponse:
    """Provides a sample ClassificationRentalResponse object."""
    return ClassificationRentalResponse(
        classification=ClassificationRentalScore(
            reasoning="This is a rental contract.",
            category=ClassificationRentalType.RENTAL_CONTRACT,
            confidence_score=0.85
        ),
        next_3_potential_categories=[
            ClassificationRentalScore(
                reasoning="This is a rental contract.",
                category=ClassificationRentalType.GENERAL_CUSTOMER,
                confidence_score=0.10
            )
        ]
    )

@pytest.fixture
def mock_genai_client(mocker, sample_classification_response) -> MagicMock:
    """Mocks the genai_client and its async methods."""
    mock_client = MagicMock()
    mock_generate_content = AsyncMock()

    # Mock the response structure from generate_content
    mock_response = MagicMock()
    mock_response.text = f"```json \n {sample_classification_response.model_dump_json()} ```"
    mock_response.parsed = sample_classification_response  # Simulate the .parsed attribute
    mock_generate_content.return_value = mock_response

    # Mock the nested structure client().aio.models.generate_content
    mock_client.aio.models.generate_content = mock_generate_content

    # Patch the client function in the module where it's used
    mocker.patch('enginepy.agents.rental_classifier.gemini.genai_client', return_value=mock_client)
    return mock_client

# --- Tests ---

def test_agent_attributes():
    """Test default attributes of the agent."""
    agent = ClassifierRentalGeminiAgent()
    assert agent.name == "ClassifierRentalGeminiAgent"
    assert agent.default_provider == "gemini"
    assert agent.default_model is not None

def test_init_default_model():
    """Test initialization uses the default model if none provided."""
    agent = ClassifierRentalGeminiAgent()
    assert agent.model == agent.default_model

def test_init_custom_model():
    """Test initialization uses the provided custom model."""
    agent = ClassifierRentalGeminiAgent(model=CUSTOM_MODEL)
    assert agent.model == CUSTOM_MODEL

def test_config(sample_classification_response):
    """Test the config() method returns correct GenerateContentConfig."""
    agent = ClassifierRentalGeminiAgent()
    config = agent.config()

    assert isinstance(config, genai_types.GenerateContentConfig)    
    assert config.response_mime_type == "application/json"
    # Check that the schema type matches the expected response model
    assert config.response_schema == ClassificationRentalResponse
    # Check that system_instruction is called and returns a Part
    assert isinstance(config.system_instruction, genai_types.Part)
    assert "Classify the given input" in config.system_instruction.text

def test_system_instruction():
    """Test the system_instruction() method generates the correct Part."""
    agent = ClassifierRentalGeminiAgent()
    part = agent.system_instruction()

    assert isinstance(part, genai_types.Part)
    assert "Classify" in part.text
    # Check if all categories are listed
    for category in ClassificationRentalType:
        assert category.value in part.text
    # Check for JSON schema format hint
    assert '"category": ""' in part.text
    assert '"confidence_score":' in part.text
    assert '"next_3_potential_categories": [' in part.text

def test_instructions():
    """Test the instructions() method wraps content correctly."""
    agent = ClassifierRentalGeminiAgent()
    contents = agent.instructions(INPUT_TEXT)

    assert isinstance(contents, list)
    assert len(contents) == 1
    content_item = contents[0]
    assert isinstance(content_item, genai_types.Content)
    assert content_item.role == "user"
    assert isinstance(content_item.parts, list)
    assert len(content_item.parts) == 1
    part_item = content_item.parts[0]
    assert isinstance(part_item, genai_types.Part)
    assert part_item.text == INPUT_TEXT

@pytest.mark.asyncio
async def test_run(mock_genai_client, sample_ctx, sample_classification_response):
    """Test the run method calls the client and returns parsed response."""
    agent = ClassifierRentalGeminiAgent(model=CUSTOM_MODEL)

    # Call the method under test
    result = await agent.run(input=INPUT_TEXT, context=sample_ctx)

    # Assertions
    mock_genai_client.aio.models.generate_content.assert_called_once()
    call_args, call_kwargs = mock_genai_client.aio.models.generate_content.call_args

    # Check arguments passed to generate_content
    assert call_kwargs.get('model') == CUSTOM_MODEL
    passed_config = call_kwargs.get('config')
    assert isinstance(passed_config, genai_types.GenerateContentConfig)
    # Could add more detailed checks on passed_config if needed

    passed_contents = call_kwargs.get('contents')
    assert isinstance(passed_contents, list)
    assert len(passed_contents) == 1
    assert passed_contents[0].parts[0].text == INPUT_TEXT

    # Check the final result
    assert result == sample_classification_response
