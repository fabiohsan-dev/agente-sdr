"""Schemas para Mídia."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MediaAssetResponse(BaseModel):
    """Schema de resposta de media asset."""

    id: UUID
    lead_id: UUID
    media_type: str
    cdn_url: str
    mime_type: str | None = None
    original_filename: str | None = None
    transcription: str | None = None
    analysis: str | None = None
    status: str
    created_at: datetime
    processed_at: datetime | None = None


class MediaProcessRequest(BaseModel):
    """Schema para request de processamento de mídia."""

    cdn_url: str
    media_type: str  # audio, image
    mime_type: str | None = None
    filename: str | None = None


class MediaProcessResponse(BaseModel):
    """Schema de resposta de processamento de mídia."""

    media_id: UUID
    status: str
    transcription: str | None = None
    analysis: str | None = None
