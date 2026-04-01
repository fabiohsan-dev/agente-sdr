"""Schemas para Leads."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LeadCreate(BaseModel):
    """Schema para criar lead."""

    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    company: str | None = None
    source: str | None = None


class LeadResponse(BaseModel):
    """Schema de resposta de lead."""

    id: UUID
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    current_state: str
    owner_mode: str
    has_booking: bool
    materials_sent: bool
    checklist_sent: bool
    no_money_flag: bool
    source: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class LeadStateUpdate(BaseModel):
    """Schema para atualizar estado do lead."""

    current_state: str
