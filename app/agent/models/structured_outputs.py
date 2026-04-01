"""Modelos de saída estruturada do agente."""

from typing import Literal

from pydantic import BaseModel, Field


class AgentStructuredOutput(BaseModel):
    """Saída estruturada do agente LangGraph."""

    # ============================================
    # RESPOSTA PARA O USUÁRIO
    # ============================================

    reply_text: str = Field(
        ...,
        description="Texto da resposta para o usuário",
    )

    # ============================================
    # ESTADO
    # ============================================

    next_state: Literal[
        "NEW",
        "QUALIFYING",
        "WAITING_PRIORITY_CONFIRMATION",
        "WAITING_FIT_CONFIRMATION",
        "WAITING_TIME",
        "WAITING_EMAIL",
        "BOOKING_IN_PROGRESS",
        "SCHEDULED",
        "POST_BOOKING_PENDING_MATERIALS",
        "POST_BOOKING_PENDING_CHECKLIST",
        "NO_MONEY",
        "CLOSED",
        "PAUSED_BY_HUMAN",
    ] = Field(
        ...,
        description="Próximo estado do lead após esta interação",
    )

    # ============================================
    # AÇÕES
    # ============================================

    actions: list[str] = Field(
        default_factory=list,
        description="Lista de ações a executar (ex: 'cancel_follow', 'send_materials', 'send_checklist')",
    )

    # ============================================
    # FLAGS DE DECISÃO
    # ============================================

    should_schedule_follow: bool = Field(
        default=False,
        description="True se deve agendar follow-up",
    )

    should_call_booking_tool: bool = Field(
        default=False,
        description="True se deve chamar ferramenta de booking (oferecer agendamento)",
    )

    should_send_materials: bool = Field(
        default=False,
        description="True se deve enviar materiais",
    )

    should_send_checklist: bool = Field(
        default=False,
        description="True se deve enviar checklist",
    )

    should_pause_ai: bool = Field(
        default=False,
        description=(
            "True se deve acionar a ferramenta Pausar IA. "
            "Usar quando: (A) lead recusa mesmo após tratamento de objeção, "
            "(B) lead diz que não tem condições financeiras, "
            "(C) lead demonstra resistência ao bot e pede humano, "
            "(D) lead encerrou elegantemente e não há mais o que fazer. "
            "ORDEM OBRIGATÓRIA: primeiro responda (reply_text), depois sinalize pause. "
            "NÃO usar para: dúvidas sobre preço, pedidos de mais info, 'vou pensar'."
        ),
    )

    # ============================================
    # METADADOS ADICIONAIS
    # ============================================

    follow_reason: str | None = Field(
        default=None,
        description="Motivo do follow-up (se should_schedule_follow=True)",
    )

    booking_context: str | None = Field(
        default=None,
        description="Contexto para o booking (se should_call_booking_tool=True)",
    )

    # ============================================
    # CLASSIFICAÇÃO DE INTENÇÃO (pelo LLM)
    # ============================================

    intent: Literal[
        "INTERESTED",
        "NOT_INTERESTED",
        "NO_MONEY",
        "ASKING_INFO",
        "ASKING_SPECIFIC_QUESTION",
        "READY_TO_BOOK",
        "NEEDS_TIME",
        "WAITING_DECISION",
        "OFF_TOPIC",
        "GREETING",
        "RESPONDING_QUESTION",
        "WANTS_PAUSE",
    ] = Field(
        default="RESPONDING_QUESTION",
        description=(
            "Intenção principal da mensagem do lead. "
            "NO_MONEY: sem dinheiro/condições. "
            "ASKING_SPECIFIC_QUESTION: pergunta sobre nicho/área/serviço. "
            "READY_TO_BOOK: quer agendar. "
            "RESPONDING_QUESTION: respondendo pergunta do SDR. "
            "WANTS_PAUSE: lead quer encerrar / pede humano / recusa definitiva."
        ),
    )

    # ============================================
    # VALIDAÇÕES
    # ============================================

    class Config:
        use_enum_values = True
