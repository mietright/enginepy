# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=too-few-public-methods
import logging
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator
from pydantic.functional_validators import model_validator

logger = logging.getLogger(__name__)

SIGNATURE_FIELD = "e:information.signature:signature"


class WithContentMode(str, Enum):
    FULL = "full"
    CHUNK = "chunk"
    SUMMARY = "summary"
    NONE = "none"


class ManagerEnum(str, Enum):
    OPENAI = "openai"
    QDRANT = "qdrant"
    NONE = "none"


class OutputFormatEnum(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"


class SplitterType(str, Enum):
    RECURSIVE = "recursive"
    CHAR = "char"
    SEMANTIC = "semantic"
    SPACY = "spacy"


class Content(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    metadata: dict[str, Any] | None = Field(default=None, title="Metadata")
    summary: str | None = Field(default="", title="Summary")
    full: str | None = Field(default="", title="Full")
    chunk: str | None = Field(default="", title="Chunk")
    title: str | None = Field(default="", title="Title")
    descr: str | None = Field(default="", title="Descr")
    tags: list[str] | None = Field(default=None, title="Tags")
    lang: str | None = Field(default="", title="Lang")
    mode: WithContentMode | None = WithContentMode.SUMMARY


class DocsQuery(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    limit: int | None = Field(default=100, description="The limit of the search results", title="Limit")
    mode: WithContentMode | None = Field(
        default=WithContentMode.SUMMARY, description="Return either the matching chunks, summary or full content"
    )
    vectordb: ManagerEnum | None = Field(default=ManagerEnum.NONE, description="vectordb to use")
    keys: list[list] | None = Field(default=None, description="The keys to return", title="Keys")
    collection_id: UUID | None = Field(default=None, description="The collection ID", title="Collection Id")
    collection_name: str | None = Field(default=None, description="collection name", title="Collection Name")
    ids: list[list] | None = Field(
        default=None, description="The ids to search, e.g [['doc', '123'], ['email', '456']]", title="Ids"
    )
    output: OutputFormatEnum | None = Field(
        default=OutputFormatEnum.JSON, description="The format to return the search results"
    )
    date_lt: datetime | None = Field(default=None, description="The date to search before", title="Date Lt")
    date_gt: datetime | None = Field(default=None, description="The date to search after", title="Date Gt")
    filters: dict[str, Any] | None = Field(default=None, title="Filters")


class DocsResponse(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    docs: list[Content] | None = Field(default=None, title="Docs")
    query: DocsQuery


class AwsPrediction(BaseModel):
    label: str = Field(..., validation_alias=AliasChoices("label", "Name"))
    score: float = Field(..., validation_alias=AliasChoices("Score", "score"))


class AwsJobDescribe(BaseModel):
    id: str = Field(default="", validation_alias=AliasChoices("JobId", "id"), serialization_alias="JobId")
    # Temporarily removed aliases to diagnose pyright error
    name: str = Field(default="")
    arn: str = Field(
        default="",
        validation_alias=AliasChoices("JobArn", "arn"),
        serialization_alias="JobArn",
    )
    status: str = Field(
        default="",
        validation_alias=AliasChoices("JobStatus", "status"),
        serialization_alias="JobStatus",
    )
    submit_time: datetime = Field(
        default_factory=datetime.now,
        validation_alias=AliasChoices("SubmitTime", "submit_time"),
        serialization_alias="SubmitTime",
    )
    end_time: datetime = Field(
        default_factory=datetime.now,
        validation_alias=AliasChoices("EndTime", "end_time"),
        serialization_alias="EndTime",
    )
    classifier_arn: str = Field(
        default="",
        validation_alias=AliasChoices("DocumentClassifierArn", "classifier_arn"),
        serialization_alias="DocumentClassifierArn",
    )
    input_data: dict[str, Any] = Field(
        default={},
        validation_alias=AliasChoices("InputDataConfig", "input_data"),
        serialization_alias="InputDataConfig",
    )
    output_data: dict[str, Any] = Field(
        default={},
        validation_alias=AliasChoices("OutputDataConfig", "output_data"),
        serialization_alias="OutputDataConfig",
    )
    role_arn: str = Field(
        default="",
        validation_alias=AliasChoices("DataAccessRoleArn", "role_arn"),
        serialization_alias="DataAccessRoleArn",
    )
    tags: dict[str, str] = Field(
        default={},
        validation_alias=AliasChoices("Tags", "tags"),
        serialization_alias="Tags",
    )


class AwsInference(BaseModel):
    input_s3: str = Field(default="")
    output_s3: str = Field(default="")
    line: str = Field(..., validation_alias=AliasChoices("Line", "line"))
    classes: list[AwsPrediction] = Field(..., validation_alias=AliasChoices("Classes", "classes"))
    document_id: str = Field(default="", validation_alias=AliasChoices("document_id", "DocumentId"))
    expected: str = Field(default="", validation_alias=AliasChoices("expected", "Expected"))
    model: str = Field(default="")


class AwsClassifierResult(BaseModel):
    job: AwsJobDescribe = Field(...)
    inference: list[AwsInference] = Field(...)
    model: str = Field(default="unknown")


class DefaultType(StrEnum):
    NO_DEFAULT = "__no_default__"
    NOT_FOUND = "__not_found__"


class EngineTypeEnum(StrEnum):
    PHONE = "phone"
    STRING = "string"
    EMAIL = "email"
    IBAN = "iban"
    SELECT = "select"
    CHECKBOX = "checkbox"
    SIGNATURE = "signature"
    YES_NO = "yes_no"
    NUMBER = "number"
    SEARCHABLE_AUTOCOMPLETE = "searchable_autocomplete"


class EngineCaseInfo(BaseModel):
    user_id: int = Field(-1)
    request_id: int = Field(-1)
    reference_number: str = Field("")
    tokenized_emails: dict = Field({})
    status: Any | None = Field(None)
    uuid: str = Field(...)


class Job(BaseModel):
    uuid: str = Field(...)
    name: str = Field(...)
    status: str | None = Field(default=None)
    result: dict | EngineCaseInfo = Field(default={})


# TODO: strip_whitespace is not working anymore
class Address(BaseModel):
    city: str = Field(..., min_length=1)  # strip_whitespace=True,
    house: str = Field(..., title="House Number", min_length=1)  # strip_whitespace=True,
    postalCode: str = Field(..., min_length=1)  # strip_whitespace=True,
    street: str = Field(..., min_length=1)  # strip_whitespace=True,


class Contact(BaseModel):
    address: Address = Field(...)
    email: str = Field(..., pattern=r"^.+@.+\..+")  # strip_whitespace=True,
    firstName: str = Field(..., min_length=1)  # strip_whitespace=True,
    lastName: str = Field(..., min_length=1)  # strip_whitespace=True,


class UtmParams(BaseModel):
    awc: str = Field("")
    utm_medium: str = Field("")
    utm_source: str = Field("")
    utm_campaign: str = Field("")
    utm_term: str = Field("")
    utm_content: str = Field("")


class EngineTrigger(BaseModel):
    trigger_id: str = Field(...)
    name: str = Field(default="")
    request_id: int | None = Field(None)
    status: dict[str, Any] | None = Field(default=None)
    client: str = Field(default="enginepy")
    attempt: int = Field(default=1)


class EngineField(BaseModel):
    field: str = Field(...)
    answer: bool | str | int | float | None = Field(None)
    type: EngineTypeEnum = Field(EngineTypeEnum.STRING)


class EngineRequest(BaseModel):
    product: str = Field(...)
    funnel: str = Field(...)
    documents: str = Field(default="[]")
    request_id: int | None = Field(default=None)
    fields: list[EngineField] = Field(...)
    documents_presign: bool = Field(default=False)


class EngineResponse(BaseModel):
    request_id: int = Field(default=-1)
    user_id: int | None = Field(default=None)
    status: int | None = Field(default=None)
    result: dict | None = Field(default=None)
    tokenized_emails: dict | None = Field(default=None)
    reference_number: str | None = Field(default=None)
    triggers: list[EngineTrigger] = Field(default=[])


class ActionTrigger(BaseModel):
    trigger_id: str = Field(...)
    name: str = Field(...)


class ActionTriggers(BaseModel):
    success: list[ActionTrigger] = Field(default=[])
    fail: list[ActionTrigger] = Field(default=[])


class MappingField(BaseModel):
    type: EngineTypeEnum = Field(default=EngineTypeEnum.STRING)
    source: str | None = Field(None)
    default: bool | str | int | float | None | DefaultType = Field(default=DefaultType.NO_DEFAULT)
    optional: bool = Field(default=False)


class EngineMapper(BaseModel):
    name: str = Field(...)
    source: Literal["heyflow", "girofunnel", "facebook"] = Field(...)
    product_name: str = Field(...)
    funnel_name: str = Field(...)
    action_triggers: ActionTriggers = Field(ActionTriggers(success=[], fail=[]))
    mapping: dict[str, MappingField] = Field({})
    all_optional: bool = Field(default=True)

    @field_validator("mapping", mode="before")
    def convert_mapping_source(cls, mapper) -> dict[str, MappingField]:
        for k, v in mapper.items():
            if isinstance(v, str):
                mapper[k] = MappingField(source=v)
        return mapper


class AgentRunCost(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    total_tokens: int | None = Field(
        default=0, description="The total number of tokens used in the agent workflow run", title="Total Tokens"
    )
    total_time: float | None = Field(
        default=0.0, description="The total time taken for the agent workflow run", title="Total Time"
    )
    total_cost: float | None = Field(
        default=0.0, description="The total cost of the agent workflow run", title="Total Cost"
    )


class WorkflowInfo(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    name: str | None = Field(default="", description="The name of the agent workflow to run", title="Name")
    wid: str | None = Field(default="", description="The ID of the agent workflow to run", title="Wid")


class ClassificationRentalScore(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    category: str = Field(..., title="Category")
    reasoning: str = Field(..., title="Reasoning")
    confidence_score: float = Field(..., title="Confidence Score")


class ClassificationRentalResponse(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    classification: ClassificationRentalScore
    next_categories: list[ClassificationRentalScore] | None = Field(default=None, title="Next Categories")


class AgentClassifierWorkflowOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    result: ClassificationRentalResponse = Field(..., description="The output data from the agent workflow")
    metadata: dict[str, Any] | None = Field(
        default=None, description="The metadata for the agent workflow run", title="Metadata"
    )
    cost: AgentRunCost | None = Field(default=None, description="The cost of the agent workflow run")
    workflow_info: WorkflowInfo | None = Field(default=None, description="The information about the agent workflow run")


class CaseRawDataInformation(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    generic: dict[str, Any] | None = Field(default=None, title="Generic")
    hearing_report: dict[str, Any] | None = Field(default=None, title="Hearing Report")
    court_result: dict[str, Any] | None = Field(default=None, title="Court Result")
    rent_index: dict[str, Any] | None = Field(default=None, title="Rent Index")
    kfa: dict[str, Any] | None = Field(default=None, title="KFA")
    kfb: dict[str, Any] | None = Field(default=None, title="KFB")


class SummaryModel(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    timeline: str = Field(default="", title="Timeline")
    summary: str = Field(default="", title="Summary")
    summary_changes: list[str] | None = Field(default=None, title="Summary Changes")
    timeline_changes: list[str] | None = Field(default=None, title="Timeline Changes")


class SummaryResponse(SummaryModel):
    model_config = ConfigDict(
        extra="allow",
    )
    last_document_id: str | None = Field(default=None, title="Last Document Id")
    last_document_date: str | None = Field(default=None, title="Last Document Date")


class Summary(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    summary_type: str = Field(..., title="Summary Type")
    payload: SummaryResponse = Field(..., title="Payload")


class RelationToolAttribute(BaseModel):
    name: str = Field(..., description="Name of the attribute")
    is_positive: bool | None = Field(
        default=None,
        description="Whether the attribute is considered a positive aspect (True) or a negative aspect (False)",
    )
    description: str = Field("", description="Description of the attribute")
    contested: bool = Field(default=True, description="Whether the attribute is contested (True) or not (False)")
    value: str | bool | int | float | None = Field(default=None, description="Value of the attribute")
    metadata: dict[str, str] = Field(default_factory=dict, description="Metadata for the attribute")

    @model_validator(mode="before")
    def validate_attribute(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "is_positive" in values and not isinstance(values["is_positive"], bool):
            values["is_positive"] = None
        if "contested" in values and not isinstance(values["contested"], bool):
            values["contested"] = True
        return values


class CaseRawData(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    address: dict[str, Any] | None = Field(default=None, title="Address")
    user: dict[str, Any] | None = Field(default=None, title="User")
    contact: dict[str, Any] | None = Field(default=None, title="Contact")
    court_data: list[dict[str, Any]] | dict[str, Any] | None = Field(default=None, title="Court Data")
    counterparties: list[dict[str, Any]] | None = Field(default=None, title="Counterparties")
    information: CaseRawDataInformation | None = Field(default=None, title="Information")
    summaries: list[Summary] | None = Field(default=None, title="Summaries")
    attributes: dict[str, list[RelationToolAttribute]] = Field(
        default_factory=dict,
        description="Dictionary of attributes with categories as keys and lists of attributes as values",
    )
