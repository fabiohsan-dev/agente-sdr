"""Schemas para Chat."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Mensagem de chat."""

    content: str
    message_type: str = "text"  # text, audio, image
    media_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Request de chat."""

    session_id: str
    message: str | None = None
    message_type: str = "text"
    media_url: str | None = None
    lead_email: str | None = None
    lead_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Response de chat."""

    reply: str
    state: str
    actions: list[str] = Field(default_factory=list)
    conversation_id: UUID | None = None
    lead_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MediaMessage(BaseModel):
    """Mensagem de mídia."""

    media_url: str
    media_type: str  # audio, image
    filename: str | None = None
    mime_type: str | None = None


class MediaRequest(BaseModel):
    """Request de processamento de mídia."""

    session_id: str
    media_url: str
    media_type: str  # audio, image
    filename: str | None = None
    mime_type: str | None = None
    lead_email: str | None = None


class MediaResponse(BaseModel):
    """Response de processamento de mídia."""

    media_id: UUID
    status: str  # pending, processing, completed, failed
    transcription: str | None = None
    analysis: str | None = None
    cdn_url: str
