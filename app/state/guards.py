"""Guards e regras hard de negócio."""

from app.domain.enums import LeadState
from app.state.lead_states import AgentState


class BusinessRules:
    """Regras hard de negócio - implementadas no código, não no prompt."""

    # ============================================
    # REGRAS DE BLOQUEIO
    # ============================================

    @staticmethod
    def should_agent_respond(state: AgentState) -> bool:
        """
        Regra 1: Se estado = PAUSED_BY_HUMAN, agente não responde.

        Esta é uma trava de segurança para handoff humano.
        """
        if state.owner_mode == "human":
            return False
        if state.current_state == LeadState.PAUSED_BY_HUMAN:
            return False
        return True

    @staticmethod
    def can_offer_booking(state: AgentState) -> bool:
        """
        Regra 2: Se estado = NO_MONEY, não oferecer agendamento.

        Lead que disse não ter dinheiro não deve receber oferta de booking.
        """
        if state.no_money_flag:
            return False
        if state.current_state == LeadState.NO_MONEY:
            return False
        if state.has_booking:
            return False
        return True

    @staticmethod
    def can_do_commercial_approach(state: AgentState) -> bool:
        """
        Regra 3: Se estado = NO_MONEY ou SCHEDULED, não fazer abordagem comercial.

        - NO_MONEY: encerrar com elegância, sem comercial
        - SCHEDULED: já está agendado, modo pós-agendamento
        """
        if state.no_money_flag:
            return False
        if state.current_state == LeadState.NO_MONEY:
            return False
        if state.current_state == LeadState.SCHEDULED:
            return False
        if state.has_booking:
            return False
        return True

    @staticmethod
    def should_restart_commercial_script(state: AgentState) -> bool:
        """
        Regra 4: Se estado = SCHEDULED, não reiniciar roteiro comercial.

        Lead já agendado deve ser respondido em modo pós-agendamento.
        """
        if state.current_state == LeadState.SCHEDULED:
            return False
        if state.has_booking:
            return False
        return True

    @staticmethod
    def should_cancel_follow_on_response(state: AgentState) -> bool:
        """
        Regra 5: Se lead responder, cancelar follow pendente.

        Lead respondeu = follow-up não é mais necessário.
        """
        # Sempre cancelar follow se lead respondeu ativamente
        return state.incoming_message is not None and len(state.incoming_message.strip()) > 0

    # ============================================
    # REGRAS DE TRANSIÇÃO DE ESTADO
    # ============================================

    @staticmethod
    def get_next_state_on_booking_confirmed(state: AgentState) -> LeadState:
        """
        Regra 6: Se booking confirmado, mudar para POST_BOOKING_PENDING_MATERIALS.
        """
        return LeadState.POST_BOOKING_PENDING_MATERIALS

    @staticmethod
    def get_next_state_on_materials_sent(state: AgentState) -> LeadState:
        """
        Regra 7: Se materiais enviados, mudar para POST_BOOKING_PENDING_CHECKLIST.
        """
        return LeadState.POST_BOOKING_PENDING_CHECKLIST

    @staticmethod
    def get_next_state_on_checklist_confirmed(state: AgentState) -> LeadState:
        """
        Regra 8: Se checklist enviado e confirmado, manter SCHEDULED.
        """
        return LeadState.SCHEDULED

    @staticmethod
    def get_next_state_on_no_money(state: AgentState) -> LeadState:
        """
        Regra 9: Se lead disse não ter dinheiro, mudar para NO_MONEY.
        """
        return LeadState.NO_MONEY

    # ============================================
    # REGRAS DE FOLLOW-UP
    # ============================================

    @staticmethod
    def should_schedule_follow(state: AgentState) -> bool:
        """
        Regra 10: Agendar follow-up apenas em estados específicos.

        Não agendar follow para:
        - NO_MONEY
        - SCHEDULED
        - PAUSED_BY_HUMAN
        - CLOSED
        """
        if state.no_money_flag:
            return False
        if state.current_state == LeadState.NO_MONEY:
            return False
        if state.current_state == LeadState.SCHEDULED:
            return False
        if state.current_state == LeadState.PAUSED_BY_HUMAN:
            return False
        if state.current_state == LeadState.CLOSED:
            return False
        return True

    # ============================================
    # REGRAS DE MÍDIA
    # ============================================

    @staticmethod
    def should_process_audio(state: AgentState) -> bool:
        """Verifica se deve processar áudio."""
        return state.incoming_message_type == "audio" and state.media_url is not None

    @staticmethod
    def should_process_image(state: AgentState) -> bool:
        """Verifica se deve processar imagem."""
        return state.incoming_message_type == "image" and state.media_url is not None

    # ============================================
    # APLICAÇÃO DE REGRAS (aplicadas no LangGraph)
    # ============================================

    @staticmethod
    def apply_hard_rules(state: AgentState) -> AgentState:
        """
        Aplica todas as regras hard ao estado atual.

        Este método é chamado no node apply_hard_rules do LangGraph.
        """
        # Verificar se agente deve responder
        if not BusinessRules.should_agent_respond(state):
            state.reply_text = None
            state.actions = []
            state.should_call_booking_tool = False
            state.should_schedule_follow = False
            state.next_state = state.current_state
            return state

        # Verificar se pode fazer abordagem comercial
        if not BusinessRules.can_do_commercial_approach(state):
            # Não aplicar roteiro comercial
            state.metadata["commercial_approach_blocked"] = True

        # Verificar se deve reiniciar script comercial
        if not BusinessRules.should_restart_commercial_script(state):
            state.metadata["restart_script_blocked"] = True

        # Verificar se deve cancelar follow
        if BusinessRules.should_cancel_follow_on_response(state):
            state.actions.append("cancel_follow")

        return state
