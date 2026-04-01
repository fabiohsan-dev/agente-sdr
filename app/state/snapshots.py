"""Snapshots das decisões do agente para debug e observabilidade."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import LeadState


class AgentSnapshot(BaseModel):
    """Snapshot de uma decisão do agente."""

    id: UUID | None = None
    lead_id: UUID
    conversation_id: UUID | None = None

    # Estado antes/depois
    state_before: LeadState | None = None
    state_after: LeadState | None = None

    # Decisão do agente
    reply_text: str | None = None
    actions: list[str] = Field(default_factory=list)
    should_schedule_follow: bool = False
    should_call_booking_tool: bool = False
    should_send_materials: bool = False
    should_send_checklist: bool = False

    # Contexto
    prompt_used: str | None = None
    model_used: str | None = None
    tools_called: list[dict[str, Any]] = Field(default_factory=list)

    # Performance
    latency_ms: int | None = None
    tokens_used: int | None = None

    # Erros
    error: str | None = None

    # Metadados
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def from_agent_state(cls, agent_state: Any) -> "AgentSnapshot":
        """Cria snapshot a partir do AgentState."""
        return cls(
            lead_id=agent_state.lead_id,
            conversation_id=agent_state.conversation_id,
            state_before=agent_state.state_before,
            state_after=agent_state.next_state or agent_state.current_state,
            reply_text=agent_state.reply_text,
            actions=agent_state.actions,
            should_schedule_follow=agent_state.should_schedule_follow,
            should_call_booking_tool=agent_state.should_call_booking_tool,
            should_send_materials=agent_state.should_send_materials,
            should_send_checklist=agent_state.should_send_checklist,
            prompt_used=agent_state.prompt_used,
            model_used=agent_state.model_used,
            tools_called=agent_state.tools_called,
            latency_ms=agent_state.latency_ms,
            tokens_used=agent_state.tokens_used,
            error=agent_state.error,
            metadata=agent_state.metadata,
        )
