"""Pydantic schemas for LLM settings API."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class LlmSettingsResponse(BaseModel):
    """Response model for GET /api/v1/settings/llm."""

    api_base: str
    model_name: str
    has_api_key: bool
    api_key_masked: str | None
    source: Literal["runtime", "env-default"]


class LlmSettingsUpdate(BaseModel):
    """Request model for PUT /api/v1/settings/llm.

    All fields are optional — omitted fields keep their current value.
    Sending ``api_key: ""`` clears the stored key.
    """

    api_base: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
