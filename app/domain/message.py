"""Modelo de Message."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import MessageDirection, MessageType


class Message(BaseModel):
    """Modelo de Mensagem."""

    id: UUID
    conversation_id: UUID
    message_type: MessageType = MessageType.TEXT
    direction: MessageDirection
    content: str | None = None

    # Mídia (quando aplicável)
    media_url: str | None = None
    media_mime_type: str | None = None
    media_filename: str | None = None
    media_transcription: str | None = None
    media_analysis: str | None = None

    # Metadados
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
