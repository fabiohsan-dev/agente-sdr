"""Node: apply_hard_rules - Aplica regras hard de negócio."""

import logging

from app.state.guards import BusinessRules
from app.state.lead_states import AgentState

logger = logging.getLogger(__name__)


async def apply_hard_rules(state: AgentState) -> AgentState:
    """
    Node de aplicação de regras hard.

    Responsabilidades:
    - Aplicar regras de bloqueio (NO_MONEY, PAUSED_BY_HUMAN)
    - Verificar se agente deve responder
    - Verificar se pode oferecer booking
    - Verificar se pode fazer abordagem comercial
    - Marcar ações necessárias (ex: cancelar follow)

    ESTE NODE É CRÍTICO: Regras aqui prevalecem sobre o prompt.
    """
    logger.debug("Iniciando aplicação de regras hard")

    # ============================================
    # VERIFICAR SE AGENTE DEVE RESPONDER
    # ============================================

    if not BusinessRules.should_agent_respond(state):
        logger.info("Agente não deve responder (PAUSED_BY_HUMAN)")
        state.reply_text = None
        state.actions = []
        state.should_schedule_follow = False
        state.should_call_booking_tool = False
        state.should_send_materials = False
        state.should_send_checklist = False
        state.next_state = state.current_state
        state.metadata["blocked_by_human"] = True
        return state

    # ============================================
    # APLICAR REGRAS GERAIS
    # ============================================

    state = BusinessRules.apply_hard_rules(state)

    # ============================================
    # VERIFICAR SE PODE OFERECER BOOKING
    # ============================================

    if not BusinessRules.can_offer_booking(state):
        state.should_call_booking_tool = False
        state.metadata["booking_blocked"] = True

        if state.no_money_flag or state.current_state.value == "NO_MONEY":
            logger.debug("Booking bloqueado: NO_MONEY")
        elif state.has_booking:
            logger.debug("Booking bloqueado: já possui booking")

    # ============================================
    # VERIFICAR SE PODE FAZER ABORDAGEM COMERCIAL
    # ============================================

    if not BusinessRules.can_do_commercial_approach(state):
        state.metadata["commercial_approach_blocked"] = True

        if state.current_state.value == "SCHEDULED":
            logger.debug("Abordagem comercial bloqueada: SCHEDULED (modo pós-agendamento)")
        elif state.no_money_flag or state.current_state.value == "NO_MONEY":
            logger.debug("Abordagem comercial bloqueada: NO_MONEY")

    # ============================================
    # VERIFICAR SE DEVE REINICIAR SCRIPT COMERCIAL
    # ============================================

    if not BusinessRules.should_restart_commercial_script(state):
        state.metadata["restart_script_blocked"] = True
        logger.debug("Reinício de script comercial bloqueado")

    # ============================================
    # VERIFICAR SE DEVE CANCELAR FOLLOW
    # ============================================

    if BusinessRules.should_cancel_follow_on_response(state):
        if "cancel_follow" not in state.actions:
            state.actions.append("cancel_follow")
        logger.debug("Follow-up será cancelado (lead respondeu)")

    # ============================================
    # REGISTRAR NO METADATA
    # ============================================

    state.metadata["hard_rules_applied"] = True

    logger.debug("Aplicação de regras hard concluída")
    return state
