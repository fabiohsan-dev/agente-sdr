"""Modelo de Conversation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Conversation(BaseModel):
    """Modelo de Conversa."""

    id: UUID
    lead_id: UUID
    session_id: str
    is_active: bool = True
    channel: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None = None
