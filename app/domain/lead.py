"""Modelo de Lead."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import LeadState, OwnerMode


class Lead(BaseModel):
    """Modelo de Lead."""

    id: UUID
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None

    # Estado atual
    current_state: LeadState = Field(default=LeadState.NEW)
    owner_mode: OwnerMode = Field(default=OwnerMode.AGENT)

    # Controle de fluxo
    has_booking: bool = False
    materials_sent: bool = False
    checklist_sent: bool = False
    no_money_flag: bool = False

    # Follow-up
    follow_step: int = 0  # Passo atual da cadência (0-4)
    follow_scheduled_at: datetime | None = None
    follow_cancelled_at: datetime | None = None

    # Metadados
    source: str | None = None
    tags: list[str] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # ============================================
    # MÉTODOS DE VERIFICAÇÃO (GUARDS)
    # ============================================

    def is_paused_by_human(self) -> bool:
        """Verifica se lead está pausado por humano."""
        return self.current_state == LeadState.PAUSED_BY_HUMAN or self.owner_mode == OwnerMode.HUMAN

    def is_no_money(self) -> bool:
        """Verifica se lead está em estado NO_MONEY."""
        return self.current_state == LeadState.NO_MONEY or self.no_money_flag

    def is_scheduled(self) -> bool:
        """Verifica se lead já está agendado."""
        return self.current_state == LeadState.SCHEDULED or self.has_booking

    def can_receive_commercial_approach(self) -> bool:
        """Verifica se lead pode receber abordagem comercial."""
        if self.is_paused_by_human():
            return False
        if self.is_no_money():
            return False
        if self.is_scheduled():
            return False
        return True

    def can_schedule_booking(self) -> bool:
        """Verifica se pode oferecer agendamento."""
        if self.is_paused_by_human():
            return False
        if self.is_no_money():
            return False
        if self.has_booking:
            return False
        return True

    def should_not_restart_commercial_script(self) -> bool:
        """Verifica se NÃO deve reiniciar roteiro comercial."""
        return self.is_scheduled()

    def needs_follow_up(self) -> bool:
        """Verifica se lead precisa de follow-up."""
        return self.current_state in {
            LeadState.QUALIFYING,
            LeadState.WAITING_PRIORITY_CONFIRMATION,
            LeadState.WAITING_FIT_CONFIRMATION,
            LeadState.WAITING_TIME,
            LeadState.WAITING_EMAIL,
        }

    def is_post_booking(self) -> bool:
        """Verifica se está em estado pós-agendamento."""
        return self.current_state in {
            LeadState.POST_BOOKING_PENDING_MATERIALS,
            LeadState.POST_BOOKING_PENDING_CHECKLIST,
            LeadState.SCHEDULED,
        }

    # ============================================
    # MÉTODOS DE TRANSIÇÃO
    # ============================================

    def mark_no_money(self) -> None:
        """Marca lead como sem dinheiro."""
        self.no_money_flag = True
        self.current_state = LeadState.NO_MONEY

    def mark_booking_created(self) -> None:
        """Marca booking criado."""
        self.has_booking = True
        self.current_state = LeadState.POST_BOOKING_PENDING_MATERIALS

    def mark_materials_sent(self) -> None:
        """Marca materiais enviados."""
        self.materials_sent = True
        self.current_state = LeadState.POST_BOOKING_PENDING_CHECKLIST

    def mark_checklist_sent(self) -> None:
        """Marca checklist enviado."""
        self.checklist_sent = True
        self.current_state = LeadState.SCHEDULED

    def mark_paused_by_human(self) -> None:
        """Marca lead como pausado por humano."""
        self.owner_mode = OwnerMode.HUMAN
        self.current_state = LeadState.PAUSED_BY_HUMAN

    def mark_agent_control(self) -> None:
        """Marca lead como sob controle do agente."""
        self.owner_mode = OwnerMode.AGENT

    def cancel_follow(self) -> None:
        """Cancela follow-up pendente."""
        self.follow_scheduled_at = None
        self.follow_cancelled_at = datetime.utcnow()
