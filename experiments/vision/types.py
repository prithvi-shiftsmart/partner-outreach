# experiments/vision/types.py
from __future__ import annotations

from pydantic import BaseModel, field_validator


class ImageData(BaseModel):
    content: bytes
    content_type: str
    size: int
    sha256: str

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        if not v.startswith("image/"):
            raise ValueError(f"content_type must start with image/, got {v}")
        return v


class Message(BaseModel):
    role: str  # "partner" or "concierge"
    content: str


class VisionRequest(BaseModel):
    images: list[ImageData]
    partner_message: str | None
    conversation_history: list[Message]
    partner_state: str


class ImageAnalysis(BaseModel):
    screen_id: str
    visible_elements: str
    error_state: str | None
    partner_problem: str
    suggested_action: str
    confidence: float
    is_app_screenshot: bool

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {v}")
        return v
