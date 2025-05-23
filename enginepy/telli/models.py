from enum import Enum
from typing import Any, Literal  # Required for specific type hints not covered by built-ins

from pydantic import BaseModel, ConfigDict, Field

# --- Enums for Status Fields ---


class TelliEventEnum(str, Enum):
    """Enum for possible Telli events."""

    CALL_ENDED = "call_ended"
    CONTACT_STATUS_CHANGED = "contact_status_changed"


class TelliWebhook(BaseModel):
    """
    Base class for Telli webhook events.

    This class is used to define the common structure of Telli webhook events.
    """

    # Allow extra fields from the API payload
    model_config = ConfigDict(extra="allow")

    event: Literal["call_ended"] = Field(..., description="The type of the event.")
    call: dict[str, Any] = Field(..., description="The detailed information about the call.")
