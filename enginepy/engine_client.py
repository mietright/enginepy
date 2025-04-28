# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=too-few-public-methods
import logging
from typing import Any, Literal

import requests
from ant31box.client.base import BaseClient

from connyex.gen.antbed import DocsResponse
from connyex.gen.enginepy import AgentClassifierWorkflowOutput
from connyex.ml.comprehend.models import AwsClassifierResult

logger = logging.getLogger(__name__)


class EngineClient(BaseClient):
    def __init__(self, endpoint: str, token: str) -> None:
        super().__init__(endpoint=endpoint, verify_tls=False, client_name="engine")
        self.token = token

    def set_token(self, token: str) -> None:
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
        return super().headers(content_type=content_type, extra=headers)

    def update_doc(self, doc_id: int, ocr_pages: list[str], searchable_pdf: str = "") -> bool:
        url = self._url("/api/zieb/documents/ocr")
        data = {
            "document_id": str(doc_id),
            "ocr": ocr_pages,
            "searchable_pdf_url": searchable_pdf,
        }
        headers = self.headers()
        resp = requests.post(
            url,
            params={},
            json=data,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        return True

    def update_doc_suggestions(self, updates: AwsClassifierResult) -> dict[str, Any]:
        url = self._url("/api/zieb/documents/update_suggestions")
        data = updates.model_dump_json()
        if isinstance(updates, AgentClassifierWorkflowOutput):
            data = updates.model_dump_json(exclude_none=True, exclude_unset=True)

        headers = self.headers()
        resp = requests.post(
            url,
            params={},
            data=data,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def update_insights(self, docs: DocsResponse) -> dict[str, Any]:
        url = self._url("/api/insights")
        data = docs.model_dump_json()
        headers = self.headers()
        resp = requests.post(
            url,
            params={},
            data=data,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
