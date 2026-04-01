"""Transições de estado do lead."""

from app.domain.enums import LeadState
from app.state.lead_states import AgentState


class StateTransitions:
    """Gerencia transições de estado do lead."""

    # Matriz de transições válidas
    VALID_TRANSITIONS = {
        LeadState.NEW: {
            LeadState.QUALIFYING,
            LeadState.NO_MONEY,
            LeadState.CLOSED,
            LeadState.PAUSED_BY_HUMAN,
        },
        LeadState.QUALIFYING: {
            LeadState.WAITING_PRIORITY_CONFIRMATION,
            LeadState.WAITING_FIT_CONFIRMATION,
            LeadState.WAITING_TIME,
            LeadState.WAITING_EMAIL,
            LeadState.BOOKING_IN_PROGRESS,
            LeadState.NO_MONEY,
            LeadState.CLOSED,
            LeadState.PAUSED_BY_HUMAN,
        },
        LeadState.WAITING_PRIORITY_CONFIRMATION: {
            LeadState.QUALIFYING,
            LeadState.WAITING_FIT_CONFIRMATION,
            LeadState.WAITING_TIME,
            LeadState.BOOKING_IN_PROGRESS,
            LeadState.NO_MONEY,
            LeadState.CLOSED,
            LeadState.PAUSED_BY_HUMAN,
        },
        LeadState.WAITING_FIT_CONFIRMATION: {
            LeadState.QUALIFYING,
            LeadState.WAITING_PRIORITY_CONFIRMATION,
            LeadState.WAITING_TIME,
            LeadState.BOOKING_IN_PROGRESS,
            LeadState.NO_MONEY,
            LeadState.CLOSED,
            LeadState.PAUSED_BY_HUMAN,
        },
        LeadState.WAITING_TIME: {
            LeadState.QUALIFYING,
            LeadState.WAITING_EMAIL,
            LeadState.BOOKING_IN_PROGRESS,
            LeadState.NO_MONEY,
            LeadState.CLOSED,
            LeadState.PAUSED_BY_HUMAN,
        },
        LeadState.WAITING_EMAIL: {
            LeadState.BOOKING_IN_PROGRESS,
            LeadState.NO_MONEY,
            LeadState.CLOSED,
            LeadState.PAUSED_BY_HUMAN,
        },
        LeadState.BOOKING_IN_PROGRESS: {
            LeadState.SCHEDULED,
            LeadState.QUALIFYING,
            LeadState.NO_MONEY,
            LeadState.CLOSED,
            LeadState.PAUSED_BY_HUMAN,
        },
        LeadState.SCHEDULED: {
            LeadState.POST_BOOKING_PENDING_MATERIALS,
            LeadState.CLOSED,
            LeadState.PAUSED_BY_HUMAN,
        },
        LeadState.POST_BOOKING_PENDING_MATERIALS: {
            LeadState.POST_BOOKING_PENDING_CHECKLIST,
            LeadState.SCHEDULED,
            LeadState.CLOSED,
            LeadState.PAUSED_BY_HUMAN,
        },
        LeadState.POST_BOOKING_PENDING_CHECKLIST: {
            LeadState.SCHEDULED,
            LeadState.CLOSED,
            LeadState.PAUSED_BY_HUMAN,
        },
        LeadState.NO_MONEY: {
            LeadState.CLOSED,
            LeadState.QUALIFYING,  # Se situação mudar
        },
        LeadState.CLOSED: {
            LeadState.NEW,  # Se reabrir
        },
        LeadState.PAUSED_BY_HUMAN: {
            LeadState.QUALIFYING,
            LeadState.SCHEDULED,
            LeadState.CLOSED,
        },
    }

    @classmethod
    def is_valid_transition(cls, from_state: LeadState, to_state: LeadState) -> bool:
        """Verifica se transição é válida."""
        if from_state not in cls.VALID_TRANSITIONS:
            return False
        return to_state in cls.VALID_TRANSITIONS[from_state]

    @classmethod
    def apply_transition(cls, state: AgentState, target_state: LeadState) -> AgentState:
        """
        Aplica transição de estado se for válida.

        Retorna o estado atualizado ou lança ValueError se transição inválida.
        """
        if not cls.is_valid_transition(state.current_state, target_state):
            raise ValueError(
                f"Transição inválida de {state.current_state.value} para {target_state.value}"
            )

        state.next_state = target_state
        return state

    @classmethod
    def get_valid_next_states(cls, current_state: LeadState) -> set[LeadState]:
        """Retorna estados válidos para transição a partir do estado atual."""
        return cls.VALID_TRANSITIONS.get(current_state, set())
