"""Testes unitários de exemplo."""


from app.domain.enums import LeadState, OwnerMode
from app.domain.lead import Lead
from app.state.guards import BusinessRules
from app.state.lead_states import AgentState


class TestLeadStates:
    """Testes para estados do lead."""

    def test_lead_initial_state(self):
        """Testa estado inicial do lead."""
        from datetime import datetime
        from uuid import uuid4

        lead = Lead(
            id=uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert lead.current_state == LeadState.NEW
        assert lead.owner_mode == OwnerMode.AGENT
        assert lead.has_booking is False
        assert lead.no_money_flag is False

    def test_lead_is_paused_by_human(self):
        """Testa verificação de pause por humano."""
        from datetime import datetime
        from uuid import uuid4

        lead = Lead(
            id=uuid4(),
            current_state=LeadState.PAUSED_BY_HUMAN,
            owner_mode=OwnerMode.HUMAN,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert lead.is_paused_by_human() is True

    def test_lead_is_no_money(self):
        """Testa verificação de no_money."""
        from datetime import datetime
        from uuid import uuid4

        lead = Lead(
            id=uuid4(),
            current_state=LeadState.NO_MONEY,
            no_money_flag=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert lead.is_no_money() is True


class TestBusinessRules:
    """Testes para regras de negócio."""

    def test_should_agent_respond_normal(self):
        """Testa se agente deve responder em estado normal."""
        from uuid import uuid4

        state = AgentState(
            lead_id=uuid4(),
            current_state=LeadState.QUALIFYING,
            owner_mode=OwnerMode.AGENT,
            incoming_message="Olá",
        )

        assert BusinessRules.should_agent_respond(state) is True

    def test_should_agent_respond_paused(self):
        """Testa se agente NÃO deve responder quando pausado."""
        from uuid import uuid4

        state = AgentState(
            lead_id=uuid4(),
            current_state=LeadState.PAUSED_BY_HUMAN,
            owner_mode=OwnerMode.HUMAN,
            incoming_message="Olá",
        )

        assert BusinessRules.should_agent_respond(state) is False

    def test_can_offer_booking_no_money(self):
        """Testa se NÃO pode oferecer booking quando no_money."""
        from uuid import uuid4

        state = AgentState(
            lead_id=uuid4(),
            current_state=LeadState.NO_MONEY,
            no_money_flag=True,
            incoming_message="Olá",
        )

        assert BusinessRules.can_offer_booking(state) is False

    def test_can_offer_booking_available(self):
        """Testa se pode oferecer booking quando disponível."""
        from uuid import uuid4

        state = AgentState(
            lead_id=uuid4(),
            current_state=LeadState.QUALIFYING,
            no_money_flag=False,
            has_booking=False,
            incoming_message="Olá",
        )

        assert BusinessRules.can_offer_booking(state) is True


class TestStateTransitions:
    """Testes para transições de estado."""

    def test_valid_transition_new_to_qualifying(self):
        """Testa transição válida de NEW para QUALIFYING."""
        from app.state.transitions import StateTransitions

        assert StateTransitions.is_valid_transition(
            LeadState.NEW,
            LeadState.QUALIFYING,
        ) is True

    def test_invalid_transition_new_to_scheduled(self):
        """Testa transição inválida de NEW para SCHEDULED."""
        from app.state.transitions import StateTransitions

        assert StateTransitions.is_valid_transition(
            LeadState.NEW,
            LeadState.SCHEDULED,
        ) is False
