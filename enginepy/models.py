from typing import Any, TypeVar

from ant31box.models import AsyncResponse as BaseAsyncResponse
from pydantic import BaseModel, ConfigDict, Field

from enginepy.agents.case_summary.models import ConnyRequestSummary, SummaryResponse
from enginepy.agents.rental_classifier.models import ClassificationRentalCtx, ClassificationRentalResponse
from enginepy.agents.summarizer.models import SummaryInput, SummaryResult
from enginepy.gen.antbed import DocsResponse, OutputFormatEnum, WithContentMode


class AsyncResponse(BaseAsyncResponse):
    @property
    def secret_key(self):
        return b"NhqPtmfle3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j-antgent"


class Docs(BaseModel):
    markdown: str | None = Field(default=None)
    docs: DocsResponse | None = Field(default=None)
    output: OutputFormatEnum = Field(default=OutputFormatEnum.JSON)
    mode: WithContentMode = Field(default=WithContentMode.SUMMARY)

    def content(self) -> DocsResponse | str | None:
        if self.output == OutputFormatEnum.JSON:
            return self.docs
        return self.markdown

    def content_str(self) -> str:
        content = self.content()
        if isinstance(content, DocsResponse):
            if content.docs is not None and len(content.docs) == 0:
                return ""
            return content.model_dump_json(exclude_none=True, exclude_unset=True, exclude_defaults=True, indent=2)
        if content is None:
            return ""
        return content


class AnyData(BaseModel):
    model_config = ConfigDict(extra="allow")


WInput = TypeVar("WInput", bound=BaseModel)
WOutput = TypeVar("WOutput", bound=BaseModel)


class AgentWorkflowInput[TInput](BaseModel):
    context: TInput = Field(..., description="The input data for the agent workflow")
    input: str = Field(default="", description="The input data for the agent workflow")


class AgentRunCost(BaseModel):
    total_tokens: int = Field(default=0, description="The total number of tokens used in the agent workflow run")
    total_time: float = Field(default=0.0, description="The total time taken for the agent workflow run")
    total_cost: float = Field(default=0.0, description="The total cost of the agent workflow run")


class WorkflowInfo(BaseModel):
    name: str = Field(default="", description="The name of the agent workflow to run")
    wid: str = Field(default="", description="The ID of the agent workflow to run")


class AgentWorkflowOutput[WOutput](BaseModel):
    model_config = ConfigDict(extra="allow")
    result: WOutput = Field(..., description="The output data from the agent workflow")
    metadata: dict[str, Any] = Field(default_factory=dict, description="The metadata for the agent workflow run")
    cost: AgentRunCost | None = Field(default=None, description="The cost of the agent workflow run")
    workflow_info: WorkflowInfo | None = Field(default=None, description="The information about the agent workflow run")


# class ClassificationInput(BaseModel):
#     content: str = Field(..., description="The content of the document to classify")
#     context: ClassificationRentalCtx = Field(None, description="The context for the classification request")


class AgentCaseSummaryWorkflowInput(AgentWorkflowInput[ConnyRequestSummary]): ...


class AgentCaseSummaryWorkflowOutput(AgentWorkflowOutput[list[SummaryResponse]]): ...


class AgentTextSummaryWorkflowOutput(AgentWorkflowOutput[SummaryResult]): ...


class AgentTextSummaryWorkflowInput(AgentWorkflowInput[SummaryInput]): ...


class AgentClassifierWorkflowInput(AgentWorkflowInput[ClassificationRentalCtx]): ...


class AgentClassifierWorkflowOutput(AgentWorkflowOutput[ClassificationRentalResponse]): ...
