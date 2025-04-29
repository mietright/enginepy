# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=too-few-public-methods
import asyncio
import json
import logging
from typing import Any, Literal

from aiohttp.client import ClientTimeout
from ant31box.client.base import BaseClient

from enginepy.models import (
    AgentClassifierWorkflowOutput,
    AwsClassifierResult,
    DocsResponse,
    EngineRequest,
    EngineTrigger,
)

logger = logging.getLogger(__name__)


class EngineClient(BaseClient):
    def __init__(self, endpoint: str, token: str) -> None:
        # Added client_name for consistency and potential logging/tracing benefits
        super().__init__(endpoint=endpoint, verify_tls=False, client_name="engine")
        self.token = token
        # self.ssl_mode is inherited from BaseClient and defaults based on verify_tls

    def set_token(self, token: str) -> None:
        """Updates the authentication token used for subsequent requests."""
        self.token = token

    def headers(
        self,
        content_type: Literal["json", "form"] | str | None = "json",
        extra: dict[str, str] | None = None,
    ) -> dict[str, str]:
        headers = {
            "Accept": "*/*",
            "token": self.token,
        }

        if extra is not None:
            headers.update(extra)
        # Ensure the base headers (like User-Agent) are included
        return super().headers(content_type=content_type, extra=headers)

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
        headers = self.headers()
        # Changed to use self.session.post with await
        resp = await self.session.post(
            url,
            params={},  # Keep params if needed, otherwise remove
            json=data,  # Use json parameter for automatic serialization and content-type
            headers=headers,
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

        headers = self.headers()
        # Changed to use self.session.post with await
        resp = await self.session.post(
            url,
            params={},  # Keep params if needed, otherwise remove
            json=data_dict,  # Use json parameter with the dictionary
            headers=headers,
            ssl=self.ssl_mode,
            timeout=ClientTimeout(total=30),
        )
        await self.log_request(resp)
        resp.raise_for_status()
        return await resp.json()

    async def get_case_data(self, request_id: int) -> dict[str, Any]:
        """
        Retrieves case data associated with a specific request ID.

        Args:
            request_id: The ID of the request for which to retrieve case data.

        Returns:
            A dictionary containing the case data.
            Note: Consider defining a specific Pydantic model for this response structure.

        Raises:
            aiohttp.ClientResponseError: If the API returns an error status (4xx or 5xx).
        """
        path = "/api/case_data"
        params = {"request_id": request_id}
        headers = self.headers()  # Default headers are suitable for GET expecting JSON
        resp = await self.session.get(
            self._url(path),
            params=params,
            headers=headers,
            ssl=self.ssl_mode,
            timeout=ClientTimeout(total=30),  # Consistent timeout
        )
        await self.log_request(resp)  # Log the request/response details
        resp.raise_for_status()
        return await resp.json()

    async def health(self) -> bool:
        """
        Checks the health of the engine API.

        Returns:
            The JSON response from the health endpoint, typically a dictionary indicating status.
            Note: Consider defining a specific Pydantic model for this response.

        Raises:
            aiohttp.ClientResponseError: If the API returns an error status (4xx or 5xx).
        """
        path: str = "/_health"
        headers = self.headers()
        resp = await self.session.get(
            self._url(path),
            headers=headers,
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
        headers = self.headers("form")  # Original used form content type
        resp = await self.session.put(
            self._url(path),
            params=params,
            headers=headers,
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
        # Note: The original implementation might have intended to pass request_id etc.
        # in the body or params of the PUT request within action_trigger.
        # The current implementation matches the provided aio.py structure.
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

        headers = self.headers("form")
        resp = await self.session.post(
            self._url(path),
            headers=headers,
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
        payload = enginereq.model_dump(exclude_none=True, exclude_unset=True)
        # Handle nested JSON field specifically
        if "fields" in payload and isinstance(payload["fields"], dict | list):
            payload["fields"] = json.dumps(payload["fields"], sort_keys=True, default=str)
        payload["request_id"] = request_id  # Set the request_id for update

        headers = self.headers("form")
        resp = await self.session.put(
            self._url(path),
            headers=headers,
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
        headers = self.headers()
        # Changed to use self.session.post with await
        resp = await self.session.post(
            url,
            params={},  # Keep params if needed, otherwise remove
            json=data_dict,  # Use json parameter with the dictionary
            headers=headers,
            ssl=self.ssl_mode,
            timeout=ClientTimeout(total=30),
        )
        await self.log_request(resp)
        resp.raise_for_status()
        return await resp.json()
