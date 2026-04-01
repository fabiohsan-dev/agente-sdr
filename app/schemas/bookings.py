"""Schemas para Bookings."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    """Schema para criar booking."""

    lead_id: UUID
    start_time: datetime
    end_time: datetime
    title: str | None = None
    description: str | None = None
    timezone: str = "America/Sao_Paulo"
    calcom_booking_id: int | None = None
    meeting_url: str | None = None
    calcom_data: dict = Field(default_factory=dict)


class BookingResponse(BaseModel):
    """Schema de resposta de booking."""

    id: UUID
    lead_id: UUID
    calcom_booking_id: int | None = None
    title: str | None = None
    description: str | None = None
    start_time: datetime
    end_time: datetime
    timezone: str
    status: str
    meeting_url: str | None = None
    created_at: datetime
    updated_at: datetime


class BookingSlotRequest(BaseModel):
    """Schema para buscar slots."""

    event_type_id: int | None = None
    start_date: str  # ISO 8601
    end_date: str  # ISO 8601


class BookingSlot(BaseModel):
    """Schema de slot disponível."""

    start_time: str
    end_time: str
    utc_offset: int = -180
