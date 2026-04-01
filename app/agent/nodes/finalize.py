"""Node: finalize - Finaliza execução e faz cleanup."""

import logging

from app.state.lead_states import AgentState

logger = logging.getLogger(__name__)


async def finalize(state: AgentState) -> AgentState:
    """
    Node de finalização.

    Responsabilidades:
    - Validar estado final
    - Garantir consistência dos dados
    - Preparar metadata final
    - Logar execução completa
    - Flush do Langfuse (se configurado)
    """
    logger.debug("Iniciando finalização")

    # ============================================
    # VALIDAR ESTADO FINAL
    # ============================================

    _validate_final_state(state)

    # ============================================
    # GARANTIR CONSISTÊNCIA
    # ============================================

    _ensure_consistency(state)

    # ============================================
    # METADATA FINAL
    # ============================================

    state.metadata["execution_completed"] = True
    state.metadata["has_reply"] = bool(state.reply_text)
    state.metadata["state_changed"] = (
        state.state_before != state.next_state
        if state.state_before and state.next_state
        else False
    )

    # ============================================
    # LANGFUSE FLUSH
    # ============================================

    try:
        from app.integrations.langfuse.tracing import get_langfuse
        langfuse = get_langfuse()
        if langfuse.is_available():
            langfuse.flush()
            logger.debug("🔵 Langfuse: flush executado")
    except Exception as e:
        logger.debug(f"Langfuse flush error: {e}")

    # ============================================
    # LOG FINAL
    # ============================================

    logger.info(
        f"Execução concluída | "
        f"lead_id={state.lead_id} | "
        f"state={state.next_state.value if state.next_state else state.current_state.value} | "
        f"latency={state.latency_ms}ms | "
        f"has_reply={bool(state.reply_text)}"
    )

    return state


def _validate_final_state(state: AgentState) -> None:
    """Valida estado final."""
    # Garantir que next_state está definido
    if state.next_state is None:
        state.next_state = state.current_state
        logger.debug("next_state não definido, usando current_state")

    # Garantir que reply_text não é vazio se não há erro
    if not state.reply_text and not state.error:
        # Se não há erro e não há reply, pode ser estado bloqueado
        if state.metadata.get("blocked_by_human"):
            logger.debug("Sem reply (blocked_by_human)")
        else:
            logger.warning("Sem reply_text e sem erro")


def _ensure_consistency(state: AgentState) -> None:
    """Garante consistência dos dados."""
    # Se NO_MONEY, garantir flags consistentes
    if state.next_state.value == "NO_MONEY" or state.no_money_flag:
        state.should_call_booking_tool = False
        state.should_schedule_follow = False
        state.no_money_flag = True

    # Se SCHEDULED, garantir flags consistentes
    if state.next_state.value == "SCHEDULED":
        state.should_call_booking_tool = False  # Já tem booking

    # Se PAUSED_BY_HUMAN, garantir que não há reply e follows cancelados
    if state.next_state.value == "PAUSED_BY_HUMAN":
        state.reply_text = None
        state.actions = []
        state.should_schedule_follow = False
        state.should_call_booking_tool = False
        state.should_send_materials = False
        state.should_send_checklist = False
        state.should_pause_ai = False  # Já processada
        # follow_step já foi resetado no maybe_call_tools ou persist_decision
