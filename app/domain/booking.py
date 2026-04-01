"""Modelo de Booking."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Booking(BaseModel):
    """Modelo de Agendamento."""

    id: UUID
    lead_id: UUID
    calcom_booking_id: int | None = None
    title: str | None = None
    description: str | None = None
    start_time: datetime
    end_time: datetime
    timezone: str = "America/Sao_Paulo"
    status: str = "confirmed"
    cancelled_at: datetime | None = None
    rescheduled_from_id: UUID | None = None
    meeting_url: str | None = None
    calcom_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
