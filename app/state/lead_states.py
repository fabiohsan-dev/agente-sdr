"""Estados do lead e contexto do agente."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import LeadState, OwnerMode
from app.domain.lead import Lead


class AgentState(BaseModel):
    """Estado completo para o agente LangGraph."""

    # ============================================
    # DADOS DE ENTRADA
    # ============================================

    # ID do lead e sessão
    lead_id: UUID | None = None
    session_id: str | None = None
    conversation_id: UUID | None = None

    # Multi-tenancy
    tenant_id: UUID | None = None

    # Mensagem recebida
    incoming_message: str | None = None
    incoming_message_type: str = "text"  # text, audio, image

    # Mídia (quando aplicável)
    media_url: str | None = None
    media_type: str | None = None
    media_transcription: str | None = None
    media_analysis: str | None = None

    # ============================================
    # ESTADO ATUAL DO LEAD
    # ============================================

    lead: Lead | None = None

    # Estado atual (denormalizado para fácil acesso)
    current_state: LeadState = LeadState.NEW
    owner_mode: OwnerMode = OwnerMode.AGENT

    # Flags do lead
    has_booking: bool = False
    materials_sent: bool = False
    checklist_sent: bool = False
    no_money_flag: bool = False

    # ============================================
    # CONTEXTO DA CONVERSA
    # ============================================

    # Histórico recente (últimas mensagens)
    recent_messages: list[dict[str, Any]] = Field(default_factory=list)

    # Contexto formatado para o prompt
    conversation_context: str = ""

    # ============================================
    # CONTEXTO SISTÊMICO (para o prompt)
    # ============================================

    system_context: dict[str, Any] = Field(default_factory=dict)

    # ============================================
    # SAÍDA DO AGENTE (preenchido pelo LangGraph)
    # ============================================

    # Resposta para o usuário
    reply_text: str | None = None

    # Próximo estado
    next_state: LeadState | None = None

    # Ações a executar
    actions: list[str] = Field(default_factory=list)

    # Flags de decisão
    should_schedule_follow: bool = False
    should_call_booking_tool: bool = False
    should_send_materials: bool = False
    should_send_checklist: bool = False
    should_pause_ai: bool = False

    # Follow-up
    follow_scheduled_for: datetime | None = None
    follow_reason: str | None = None

    # ============================================
    # METADADOS DE EXECUÇÃO
    # ============================================

    # Estado antes da decisão (para snapshot)
    state_before: LeadState | None = None

    # Prompt usado
    prompt_used: str | None = None

    # Modelo usado
    model_used: str | None = None

    # Tools chamadas
    tools_called: list[dict[str, Any]] = Field(default_factory=list)

    # Performance
    latency_ms: int | None = None
    tokens_used: int | None = None

    # Erros
    error: str | None = None

    # Metadata adicional
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ============================================
    # MÉTODOS DE CONSTRUÇÃO DE CONTEXTO
    # ============================================

    def build_system_context(self) -> dict[str, Any]:
        """Constrói contexto sistêmico para o prompt."""
        return {
            "current_state": self.current_state.value,
            "owner_mode": self.owner_mode.value,
            "has_booking": self.has_booking,
            "materials_sent": self.materials_sent,
            "checklist_sent": self.checklist_sent,
            "no_money_flag": self.no_money_flag,
            "latest_media_type": self.media_type,
            "latest_media_url": self.media_url,
            "latest_media_analysis": self.media_analysis or self.media_transcription,
        }

    def update_from_lead(self, lead: Lead) -> None:
        """Atualiza estado a partir do lead."""
        self.lead = lead
        self.current_state = lead.current_state
        self.owner_mode = lead.owner_mode
        self.has_booking = lead.has_booking
        self.materials_sent = lead.materials_sent
        self.checklist_sent = lead.checklist_sent
        self.no_money_flag = lead.no_money_flag
        self.lead_id = lead.id

    def mark_state_before(self) -> None:
        """Marca estado antes da decisão (para snapshot)."""
        self.state_before = self.current_state
