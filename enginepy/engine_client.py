# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=too-few-public-methods
import asyncio
import json
import logging
from typing import Any, Literal

from aiohttp.client import ClientTimeout
from ant31box.client.base import BaseClient

from enginepy.config import EngineConfigSchema
from enginepy.gen.cagents import SummaryResponseOutput
from enginepy.models import (
    AgentClassifierWorkflowOutput,
    AwsClassifierResult,
    CaseRawData,
    DocsResponse,
    EngineRequest,
    EngineTokenName,
    EngineTrigger,
)
from enginepy.telli.models import TelliWebhook

logger = logging.getLogger(__name__)


API_ENDPOINT_METADATA: dict[str, dict[str, Any]] = {
    "update_doc": {
        "tokens": [EngineTokenName.ZIEB, EngineTokenName.ADMIN],
        "path": "/api/zieb/documents/ocr",
        "method": "POST",
    },
    "update_doc_suggestions": {
        "tokens": [EngineTokenName.ZIEB, EngineTokenName.ADMIN],
        "path": "/api/zieb/documents/update_suggestions",
        "method": "POST",
    },
    "get_case_data_all": {
        "tokens": [EngineTokenName.ZIEB, EngineTokenName.ADMIN],
        "path": "/api/case_data",
        "method": "GET",
    },
    "get_case_data": {
        "tokens": [EngineTokenName.ZIEB, EngineTokenName.ADMIN],
        "path": "/api/case_data",
        "method": "GET",
    },
    "health": {"tokens": [], "path": "/_health", "method": "GET"},
    "action_trigger": {
        "tokens": [EngineTokenName.ADMIN],
        "path": "/api/admin/action_triggers/{trigger_id}",
        "method": "PUT",
    },
    "create_request": {
        "tokens": [EngineTokenName.ADMIN],
        "path": "/api/admin/data_source",
        "method": "POST",
    },
    "update_request": {
        "tokens": [EngineTokenName.ADMIN],
        "path": "/api/admin/data_source",
        "method": "PUT",
    },
    "update_insights": {
        "tokens": [EngineTokenName.ZIEB, EngineTokenName.ADMIN],
        "path": "/api/insights",
        "method": "POST",
    },
    "scheduled_call_response": {
        "tokens": [EngineTokenName.ADMIN],
        "path": "/api/scheduled_call_response",
        "method": "POST",
    },
    "update_case_summary": {
        "tokens": [EngineTokenName.ADMIN],
        "path": "/api/case_summaries/{request_id}",
        "method": "POST",
    },
}


class EngineClient(BaseClient):
    def __init__(
        self,
        config: EngineConfigSchema | None = None,
        endpoint: str | None = None,
        token: str | None = None,
    ) -> None:
        if config:
            _endpoint = config.endpoint
            self.config = config
        elif endpoint and token:
            logger.warning(
                "Initializing EngineClient with endpoint and token is deprecated. Please use a config object."
            )
            _endpoint = endpoint
            self.config = EngineConfigSchema(endpoint=endpoint, token=token)
        else:
            raise ValueError("Must provide either a 'config' object or 'endpoint' and 'token'.")

        super().__init__(endpoint=_endpoint, verify_tls=False, client_name="engine")

    @property
    def token(self) -> str:
        return self.config.token

    def set_token(self, token: str) -> None:
        """Updates the default authentication token used for subsequent requests."""
        self.config.token = token

    def _get_token(self, token_prefs: list[EngineTokenName] | None = None) -> str:
        """
        Resolves which token to use based on a priority list.

        Iterates through the preferred token names, returning the first one found in the
        configuration. If none are found, it falls back to the default token.
        """
        if token_prefs:
            for token_name in token_prefs:
                # getattr on config.tokens (pydantic model)
                token_value = getattr(self.config.tokens, token_name.value.lower(), None)
                if token_value:
                    return token_value
        # Fallback to the main token
        if self.config.token:
            return self.config.token
        raise ValueError("No suitable token found for the request.")

    def headers(
        self,
        content_type: Literal["json", "form"] | str | None = "json",
        extra: dict[str, str] | None = None,
        token: str | None = None,
    ) -> dict[str, str]:
        _token = token or self.config.token
        logger.info("Using token: %s", _token)
        headers_dict = {
            "Accept": "*/*",
            "token": _token,
        }

        if extra is not None:
            headers_dict.update(extra)
        # Ensure the base headers (like User-Agent) are included
        return super().headers(content_type=content_type, extra=headers_dict)

    async def update_doc(self, doc_id: int, ocr_pages: list[str], searchable_pdf: str = "") -> bool:
        """
        Updates a document's OCR content and optionally its searchable PDF URL.

        Args:
            doc_id: The ID of the document to update.
            ocr_pages: A list of strings, where each string is the OCR text of a page.
            searchable_pdf: The URL to the searchable PDF version of the document.

        Returns:
            True if the update was successful.

        Raises:
            aiohttp.ClientResponseError: If the API returns an error status (4xx or 5xx).
        """
        url = self._url("/api/zieb/documents/ocr")
        data = {
            "document_id": str(doc_id),
            "ocr": ocr_pages,
            "searchable_pdf_url": searchable_pdf,
        }
        token = self._get_token(API_ENDPOINT_METADATA["update_doc"]["tokens"])
        request_headers = self.headers(token=token)
        # Changed to use self.session.post with await
        resp = await self.session.post(
            url,
            params={},  # Keep params if needed, otherwise remove
            json=data,  # Use json parameter for automatic serialization and content-type
            headers=request_headers,
            ssl=self.ssl_mode,
            timeout=ClientTimeout(total=30),
        )
        await self.log_request(resp)
        resp.raise_for_status()
        # No need to process json response, just return True on success
        return True

    async def update_doc_suggestions(
        self, updates: AwsClassifierResult | AgentClassifierWorkflowOutput
    ) -> dict[str, Any]:
        """
        Updates document suggestions based on classifier results.

        Args:
            updates: An object containing the classification results (either from AWS or Agent Workflow).

        Returns:
            A dictionary containing the API response.
            Note: Consider defining a specific Pydantic model for this response.

        Raises:
            aiohttp.ClientResponseError: If the API returns an error status (4xx or 5xx).
        """
        url = self._url("/api/zieb/documents/update_suggestions")
        # Use model_dump for the dictionary, pass it to the json parameter
        data_dict = updates.model_dump(exclude_none=True, exclude_unset=True)

        token = self._get_token(API_ENDPOINT_METADATA["update_doc_suggestions"]["tokens"])
        request_headers = self.headers(token=token)
        # Changed to use self.session.post with await
        resp = await self.session.post(
            url,
            params={},  # Keep params if needed, otherwise remove
            json=data_dict,  # Use json parameter with the dictionary
            headers=request_headers,
            ssl=self.ssl_mode,
            timeout=ClientTimeout(total=30),
        )
        await self.log_request(resp)
        resp.raise_for_status()
        return await resp.json()

    async def get_case_data_all(
        self, request_id: int, with_summary: bool = False, with_wwm: bool = True
    ) -> dict[str, Any]:
        """
        Retrieves case data associated with a specific request ID.

        Args:
            request_id: The ID of the request for which to retrieve case data.
            with_summary: Flag to indicate if summary should be included.

        Returns:
            A dictionary containing the case data.
            Note: Consider defining a specific Pydantic model for this response structure.

        Raises:
            aiohttp.ClientResponseError: If the API returns an error status (4xx or 5xx).
        """
        path = "/api/case_data"
        params = {
            "request_id": request_id,
            "with_summary": str(with_summary).lower(),
            "with_wwm": str(with_wwm).lower(),
        }
        token = self._get_token(API_ENDPOINT_METADATA["get_case_data_all"]["tokens"])
        request_headers = self.headers(token=token)  # Default headers are suitable for GET expecting JSON
        resp = await self.session.get(
            self._url(path),
            params=params,
            headers=request_headers,
            ssl=self.ssl_mode,
            timeout=ClientTimeout(total=30),  # Consistent timeout
        )
        await self.log_request(resp)  # Log the request/response details
        resp.raise_for_status()
        return await resp.json()

    async def get_case_data(self, request_id: int, with_summary: bool = False, with_wwm: bool = True) -> CaseRawData:
        """
        Retrieves case data associated with a specific request ID and validates into CaseRawData.

        Args:
            request_id: The ID of the request for which to retrieve case data.
            with_summary: Flag to indicate if summary should be included.

        Returns:
            A CaseRawData object containing the validated case data.

        Raises:
            aiohttp.ClientResponseError: If the API returns an error status (4xx or 5xx).
            pydantic.ValidationError: If the response data fails validation against CaseRawData.
        """
        res = await self.get_case_data_all(request_id, with_summary, with_wwm)
        return CaseRawData.model_validate(res)

    async def health(self) -> bool:
        """
        Checks the health of the engine API.

        Returns:
            True if the health endpoint returns a 200 status, False otherwise.

        Raises:
            aiohttp.ClientResponseError: If the API returns an error status (4xx or 5xx) other than 200.
        """
        path: str = "/_health"
        token = self._get_token(API_ENDPOINT_METADATA["health"]["tokens"])
        request_headers = self.headers(token=token)
        resp = await self.session.get(
            self._url(path),
            headers=request_headers,
            ssl=self.ssl_mode,
            timeout=ClientTimeout(total=10),  # Shorter timeout for health check
        )
        # Log request without body/params for GET
        await self.log_request(resp)
        resp.raise_for_status()
        return resp.status == 200

    async def action_trigger(self, engine_trigger: EngineTrigger) -> EngineTrigger:
        """
        Sends a PUT request to action a specific trigger.

        Note: This method mutates the `status` field of the input `engine_trigger` object.

        Args:
            engine_trigger: An EngineTrigger object containing trigger details (trigger_id, request_id, etc.).

        Returns:
            The updated EngineTrigger object with its status field populated from the API response.

        Raises:
            aiohttp.ClientResponseError: If the API returns an error status (4xx or 5xx).
        """
        path = f"/api/admin/action_triggers/{engine_trigger.trigger_id}"
        # Params should include query parameters
        params = engine_trigger.model_dump(include={"request_id", "client", "attempt"}, exclude_none=True)
        token = self._get_token(API_ENDPOINT_METADATA["action_trigger"]["tokens"])
        request_headers = self.headers("form", token=token)  # Original used form content type
        resp = await self.session.put(
            self._url(path),
            params=params,
            headers=request_headers,
            ssl=self.ssl_mode,
            timeout=ClientTimeout(total=30),
            # No body for this specific PUT in the original code
        )
        await self.log_request(resp)  # BaseClient.log_request handles response details
        resp.raise_for_status()
        engine_trigger.status = await resp.json()  # Assuming status is updated based on response
        return engine_trigger

    async def action_triggers(self, request_id: int, triggers: list[dict[str, str]]) -> list[EngineTrigger]:
        """
        Actions multiple triggers concurrently using asyncio.gather.

        Args:
            request_id: The request ID associated with these triggers.
            triggers: A list of dictionaries, each representing a trigger with keys like
                      'name', 'trigger_id', and optionally 'attempt'.

        Returns:
            A list of EngineTrigger objects, each updated with the status from the API response.

        Raises:
            aiohttp.ClientResponseError: If any of the underlying `action_trigger` calls fail.
            Exception: If `asyncio.gather` encounters other errors.
        """
        tasks = [
            self.action_trigger(
                EngineTrigger(
                    request_id=request_id,
                    name=trigger["name"],
                    trigger_id=trigger["trigger_id"],
                    attempt=int(trigger.get("attempt", 1)),  # Default to 1 if not provided
                )
            )
            for trigger in triggers
        ]
        results = await asyncio.gather(*tasks)
        return list(results)

    async def create_request(self, enginereq: EngineRequest) -> Any:
        """
        Creates a new data source request in the engine.

        Args:
            enginereq: An EngineRequest object containing the details for the new request.

        Returns:
            The JSON response from the API, typically containing details of the created request (e.g., request_id).
            Note: Consider defining a specific Pydantic model for this response.

        Raises:
            aiohttp.ClientResponseError: If the API returns an error status (4xx or 5xx).
        """
        path = "/api/admin/data_source"
        # Prepare payload as a dictionary for form data
        payload = enginereq.model_dump(exclude_none=True, exclude_unset=True)
        # Handle nested JSON field specifically, as in original code
        if "fields" in payload and isinstance(payload["fields"], dict | list):
            payload["fields"] = json.dumps(payload["fields"], sort_keys=True, default=str)
        payload["request_id"] = None  # Explicitly set to None for creation

        token = self._get_token(API_ENDPOINT_METADATA["create_request"]["tokens"])
        request_headers = self.headers("form", token=token)
        resp = await self.session.post(
            self._url(path),
            headers=request_headers,
            ssl=self.ssl_mode,
            data=payload,  # Use data for form encoding
            timeout=ClientTimeout(total=30),
        )
        await self.log_request(resp)  # BaseClient.log_request handles response details
        resp.raise_for_status()
        return await resp.json()

    async def update_request(self, request_id: int, enginereq: EngineRequest) -> Any:
        """
        Updates an existing data source request in the engine.

        Args:
            request_id: The ID of the request to update.
            enginereq: An EngineRequest object containing the updated details.

        Returns:
            The JSON response from the API, typically confirming the update.
            Note: Consider defining a specific Pydantic model for this response.

        Raises:
            aiohttp.ClientResponseError: If the API returns an error status (4xx or 5xx).
        """
        path = "/api/admin/data_source"
        # Prepare payload as a dictionary for form data
        payload = enginereq.model_dump()
        payload["fields"] = json.dumps(payload["fields"], sort_keys=True, default=str)
        payload["request_id"] = request_id  # Set the request_id for update

        token = self._get_token(API_ENDPOINT_METADATA["update_request"]["tokens"])
        request_headers = self.headers("form", token=token)
        resp = await self.session.put(
            self._url(path),
            headers=request_headers,
            ssl=self.ssl_mode,
            data=payload,  # Use data for form encoding
            params={},  # Original had empty params for PUT
            timeout=ClientTimeout(total=30),
        )
        await self.log_request(resp)  # BaseClient.log_request handles response details
        resp.raise_for_status()
        return await resp.json()

    async def update_insights(self, docs: DocsResponse) -> dict[str, Any]:
        """
        Updates insights based on the provided document information.

        Args:
            docs: A DocsResponse object containing the documents to update insights for.

        Returns:
            A dictionary containing the API response.
            Note: Consider defining a specific Pydantic model for this response.

        Raises:
            aiohttp.ClientResponseError: If the API returns an error status (4xx or 5xx).
        """
        url = self._url("/api/insights")
        # Use model_dump for the dictionary, pass it to the json parameter
        data_dict = docs.model_dump(exclude_none=True, exclude_unset=True)
        token = self._get_token(API_ENDPOINT_METADATA["update_insights"]["tokens"])
        request_headers = self.headers(token=token)
        # Changed to use self.session.post with await
        resp = await self.session.post(
            url,
            params={},  # Keep params if needed, otherwise remove
            json=data_dict,  # Use json parameter with the dictionary
            headers=request_headers,
            ssl=self.ssl_mode,
            timeout=ClientTimeout(total=30),
        )
        await self.log_request(resp)
        resp.raise_for_status()
        return await resp.json()

    async def scheduled_call_response(self, telli_event: TelliWebhook) -> dict[str, Any]:
        """
        Sends a Telli webhook event for a scheduled call to the engine.

        Args:
            telli_event: A TelliWebhook object containing the event details.

        Returns:
            A dictionary containing the API response.
            Note: Consider defining a specific Pydantic model for this response.

        Raises:
            aiohttp.ClientResponseError: If the API returns an error status (4xx or 5xx).
        """
        url = self._url("/api/scheduled_call_response")
        data_dict = json.loads(telli_event.model_dump_json(exclude_none=True, exclude_unset=True))
        token = self._get_token(API_ENDPOINT_METADATA["scheduled_call_response"]["tokens"])
        request_headers = self.headers(token=token)  # Default content_type is 'json'

        resp = await self.session.post(
            url,
            json=data_dict,
            headers=request_headers,
            ssl=self.ssl_mode,
            timeout=ClientTimeout(total=30),
        )
        await self.log_request(resp)
        resp.raise_for_status()
        return await resp.json()

    async def update_case_summary(self, request_id: int, summary: list[SummaryResponseOutput]) -> dict[str, Any]:
        """
        Updates the case summary for a given request.

        Args:
            request_id: The ID of the request to update.
            summary: A list of summary response objects.

        Returns:
            A dictionary containing the API response.

        Raises:
            aiohttp.ClientResponseError: If the API returns an error status (4xx or 5xx).
        """
        url = self._url(f"/api/case_summaries/{request_id}")
        # The payload is the list of summary objects. `aiohttp` will serialize it.
        data = [item.model_dump(exclude_none=True) for item in summary]
        token = self._get_token(API_ENDPOINT_METADATA["update_case_summary"]["tokens"])
        request_headers = self.headers(token=token)
        resp = await self.session.post(
            url,
            json=data,
            headers=request_headers,
            ssl=self.ssl_mode,
            timeout=ClientTimeout(total=30),
        )
        await self.log_request(resp)
        resp.raise_for_status()
        return await resp.json()
