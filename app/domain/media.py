"""Modelo de MediaAsset."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import MediaStatus, MediaType


class MediaAsset(BaseModel):
    """Modelo de Arquivo de Mídia."""

    id: UUID
    lead_id: UUID
    conversation_id: UUID | None = None
    message_id: UUID | None = None
    media_type: MediaType
    cdn_url: str  # URL original da CDN - fonte de verdade
    mime_type: str | None = None
    original_filename: str | None = None

    # Processamento (contexto auxiliar)
    transcription: str | None = None  # Apenas auxiliar, não substitui original
    analysis: str | None = None  # Apenas auxiliar, não substitui original
    status: MediaStatus = MediaStatus.PENDING

    # Metadados
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    processed_at: datetime | None = None
