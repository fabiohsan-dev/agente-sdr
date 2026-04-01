"""Node: decide_stage - Decide estágio e próxima ação."""

import logging

from app.domain.enums import LeadState
from app.state.lead_states import AgentState

logger = logging.getLogger(__name__)


async def decide_stage(state: AgentState) -> AgentState:
    """
    Node de decisão de estágio.

    Responsabilidades:
    - Analisar estado atual + intenção
    - Decidir próximo estado
    - Decidir ações necessárias
    - Preparar flags para tools
    """
    logger.debug("Iniciando decisão de estágio")

    # Se já está em estado terminal ou bloqueado, manter
    if state.current_state.value in ("CLOSED", "PAUSED_BY_HUMAN"):
        state.next_state = state.current_state
        logger.debug(f"Estado terminal: {state.current_state.value}")
        return state

    # Se NO_MONEY foi detectado, mudar estado
    if state.no_money_flag or state.metadata.get("no_money_detected"):
        state.next_state = LeadState.NO_MONEY
        state.actions.append("mark_no_money")
        logger.info("Estado mudado para NO_MONEY")
        return state

    # ============================================
    # DECISÃO BASEADA NO ESTADO ATUAL
    # ============================================

    intent = state.metadata.get("intent", "UNKNOWN")

    match state.current_state:
        case LeadState.NEW:
            state.next_state = LeadState.QUALIFYING
            state.metadata["stage_action"] = "iniciar_qualificacao"

        case LeadState.QUALIFYING:
            state.next_state = _decide_qualifying_next(state, intent)
            state.metadata["stage_action"] = "continuar_qualificacao"

        case LeadState.WAITING_PRIORITY_CONFIRMATION:
            state.next_state = _handle_waiting_state(state, intent)
            state.metadata["stage_action"] = "confirmar_prioridade"

        case LeadState.WAITING_FIT_CONFIRMATION:
            state.next_state = _handle_waiting_state(state, intent)
            state.metadata["stage_action"] = "confirmar_fit"

        case LeadState.WAITING_TIME:
            state.next_state = _handle_waiting_time(state, intent)
            state.metadata["stage_action"] = "confirmar_tempo"

        case LeadState.WAITING_EMAIL:
            state.next_state = _handle_waiting_email(state, intent)
            state.metadata["stage_action"] = "coletar_email"

        case LeadState.BOOKING_IN_PROGRESS:
            state.next_state = _handle_booking_in_progress(state, intent)
            state.metadata["stage_action"] = "aguardar_booking"

        case LeadState.SCHEDULED:
            state.next_state = LeadState.SCHEDULED
            state.metadata["stage_action"] = "pos_agendamento"

        case LeadState.POST_BOOKING_PENDING_MATERIALS:
            state.next_state = _handle_post_booking_materials(state, intent)
            state.metadata["stage_action"] = "enviar_materiais"

        case LeadState.POST_BOOKING_PENDING_CHECKLIST:
            state.next_state = _handle_post_booking_checklist(state, intent)
            state.metadata["stage_action"] = "enviar_checklist"

        case _:
            state.next_state = state.current_state
            state.metadata["stage_action"] = "manter_estado"

    # ============================================
    # DECIDIR FLAGS DE AÇÃO
    # ============================================

    _decide_action_flags(state)

    logger.debug(f"Próximo estado decidido: {state.next_state.value}")
    return state


def _decide_qualifying_next(state: AgentState, intent: str) -> LeadState:
    """Decide próximo estado a partir de QUALIFYING."""
    if intent == "READY_TO_BOOK":
        return LeadState.BOOKING_IN_PROGRESS
    elif intent == "NEEDS_TIME":
        return LeadState.WAITING_PRIORITY_CONFIRMATION
    elif intent == "NOT_INTERESTED":
        return LeadState.CLOSED
    elif intent in ("ASKING_SPECIFIC_QUESTION", "ASKING_INFO"):
        # Lead está perguntando — manter em QUALIFYING para que o LLM responda
        # com postura consultiva (AAB) e continue o script normalmente.
        return LeadState.QUALIFYING
    else:
        return LeadState.QUALIFYING  # Continuar qualificando


def _handle_waiting_state(state: AgentState, intent: str) -> LeadState:
    """Handle para estados WAITING_* genéricos."""
    if intent == "NOT_INTERESTED":
        return LeadState.CLOSED
    # Qualquer resposta que não seja negativa avança o funil.
    # O LLM classifica intenções como READY_TO_BOOK, INTERESTED, CONFIRMING, etc.
    # Não bloquear o funil por um enum exato — se o lead respondeu, avançar.
    _NEGATIVE_INTENTS = {"NOT_INTERESTED", "NO_MONEY", "UNSUBSCRIBE", "UNKNOWN"}
    if intent not in _NEGATIVE_INTENTS:
        # Avança para o PRÓXIMO estado na sequência do funil
        _NEXT_STATE_MAP = {
            LeadState.WAITING_PRIORITY_CONFIRMATION: LeadState.WAITING_FIT_CONFIRMATION,
            LeadState.WAITING_FIT_CONFIRMATION: LeadState.WAITING_TIME,
        }
        return _NEXT_STATE_MAP.get(state.current_state, state.current_state)
    return state.current_state  # Manter aguardando


def _handle_waiting_time(state: AgentState, intent: str) -> LeadState:
    """Handle para WAITING_TIME."""
    if intent == "READY_TO_BOOK":
        return LeadState.WAITING_EMAIL
    elif intent == "NOT_INTERESTED":
        return LeadState.CLOSED
    else:
        return LeadState.WAITING_TIME


def _handle_waiting_email(state: AgentState, intent: str) -> LeadState:
    """Handle para WAITING_EMAIL."""
    if intent == "NOT_INTERESTED":
        return LeadState.CLOSED
    # Se lead forneceu algo parecido com email (tem @) ou mensagem não vazia → avançar.
    msg = (state.incoming_message or "").strip()
    if msg and ("@" in msg or len(msg) > 5):
        # Salvar email no metadata para o BookingService usar
        if "@" in msg:
            # Extrair email via regex (mais robusto que split)
            import re
            email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', msg)
            if email_match:
                state.metadata["lead_email"] = email_match.group(0)
            else:
                state.metadata["lead_email"] = msg.split()[0]
        # P0-FIX: Ir para BOOKING_IN_PROGRESS (não SCHEDULED) — o booking real
        # será criado pelo Cal.com no maybe_call_tools, e só depois avança para SCHEDULED.
        state.metadata["booking_from_email_step"] = True
        return LeadState.BOOKING_IN_PROGRESS
    return LeadState.WAITING_EMAIL


def _handle_booking_in_progress(state: AgentState, intent: str) -> LeadState:
    """Handle para BOOKING_IN_PROGRESS."""
    if intent == "NOT_INTERESTED":
        return LeadState.CLOSED
    # Avança para SCHEDULED — o estado BOOKING_IN_PROGRESS já representa que o
    # lead aceitou. A confirmação externa (Cal.com) é assíncrona e não bloqueia
    # o fluxo. Se booking_confirmed vier do serviço externo, também aceita.
    return LeadState.SCHEDULED


def _handle_post_booking_materials(state: AgentState, intent: str) -> LeadState:
    """Handle para POST_BOOKING_PENDING_MATERIALS."""
    if intent == "NOT_INTERESTED":
        return LeadState.CLOSED
    # Materiais enviados OU lead respondeu positivamente → avançar para checklist.
    _NEGATIVE_INTENTS = {"NOT_INTERESTED", "NO_MONEY", "UNSUBSCRIBE", "UNKNOWN"}
    if state.metadata.get("materials_sent") or intent not in _NEGATIVE_INTENTS:
        return LeadState.POST_BOOKING_PENDING_CHECKLIST
    return LeadState.POST_BOOKING_PENDING_MATERIALS


def _handle_post_booking_checklist(state: AgentState, intent: str) -> LeadState:
    """Handle para POST_BOOKING_PENDING_CHECKLIST."""
    if intent == "NOT_INTERESTED":
        return LeadState.CLOSED
    # Checklist enviado OU lead confirmou recebimento → avançar para SCHEDULED.
    # A flag checklist_sent pode vir do metadata (serviço externo) ou ser dispensada
    # quando o lead responde positivamente (qualquer intenção não-negativa).
    _NEGATIVE_INTENTS = {"NOT_INTERESTED", "NO_MONEY", "UNSUBSCRIBE", "UNKNOWN"}
    if state.metadata.get("checklist_sent") or intent not in _NEGATIVE_INTENTS:
        return LeadState.SCHEDULED
    return LeadState.POST_BOOKING_PENDING_CHECKLIST


def _decide_action_flags(state: AgentState) -> None:
    """Decide flags de ação baseado no estado."""
    # Booking — dispara na transição WAITING_EMAIL → BOOKING_IN_PROGRESS
    # (ou SCHEDULED, caso o LLM force via fast-track)
    if state.next_state in (LeadState.BOOKING_IN_PROGRESS, LeadState.SCHEDULED):
        if state.current_state in (LeadState.WAITING_EMAIL, LeadState.BOOKING_IN_PROGRESS):
            state.should_call_booking_tool = True

    # Follow-up
    if state.next_state in (
        LeadState.QUALIFYING,
        LeadState.WAITING_PRIORITY_CONFIRMATION,
        LeadState.WAITING_FIT_CONFIRMATION,
    ):
        if state.metadata.get("intent") not in ("NOT_INTERESTED", "NO_MONEY"):
            state.should_schedule_follow = True
            state.follow_reason = "Continuar qualificação"

    # Materiais
    if state.next_state == LeadState.POST_BOOKING_PENDING_MATERIALS:
        state.should_send_materials = True

    # Checklist
    if state.next_state == LeadState.POST_BOOKING_PENDING_CHECKLIST:
        state.should_send_checklist = True
