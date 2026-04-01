"""Node: persist_decision - Persiste decisão no banco."""

import logging

from app.domain.enums import EventType
from app.repositories.agent_snapshots_repository import AgentSnapshotsRepository
from app.repositories.events_repository import EventsRepository
from app.repositories.leads_repository import LeadsRepository
from app.repositories.messages_repository import MessagesRepository
from app.state.lead_states import AgentState

logger = logging.getLogger(__name__)


async def persist_decision(state: AgentState) -> AgentState:
    """
    Node de persistência de decisão.

    Responsabilidades:
    - Salvar snapshot da decisão do agente
    - Atualizar estado do lead no banco
    - Salvar mensagem de resposta
    - Registrar eventos
    - Executar ações de estado (mark_no_money, etc.)
    """
    logger.debug("Iniciando persistência de decisão")

    # Se não há lead ou conversation, não persistir
    if not state.lead_id or not state.conversation_id:
        logger.warning("Não há lead_id ou conversation_id para persistir")
        return state

    # Se há erro, não persistir (apenas logar)
    if state.error:
        logger.warning(f"Erro no estado, não persistindo: {state.error}")
        return state

    try:
        # ============================================
        # SALVAR SNAPSHOT DA DECISÃO
        # ============================================

        await _save_snapshot(state)

        # ============================================
        # ATUALIZAR ESTADO DO LEAD
        # ============================================

        await _update_lead_state(state)

        # ============================================
        # SALVAR MENSAGEM DE RESPOSTA
        # ============================================

        if state.reply_text:
            await _save_outbound_message(state)

        # ============================================
        # REGISTRAR EVENTOS
        # ============================================

        await _register_events(state)

        # ============================================
        # EXECUTAR AÇÕES DE ESTADO
        # ============================================

        await _execute_state_actions(state)

        logger.debug("Persistência de decisão concluída")

    except Exception as e:
        logger.error(f"Erro na persistência: {e}")
        state.metadata["persist_error"] = str(e)

    return state


async def _save_snapshot(state: AgentState) -> None:
    """Salva snapshot da decisão."""
    repo = AgentSnapshotsRepository()
    await repo.create(
        lead_id=state.lead_id,
        conversation_id=state.conversation_id,
        state_before=state.state_before,
        state_after=state.next_state or state.current_state,
        reply_text=state.reply_text,
        actions=state.actions,
        should_schedule_follow=state.should_schedule_follow,
        should_call_booking_tool=state.should_call_booking_tool,
        should_send_materials=state.should_send_materials,
        should_send_checklist=state.should_send_checklist,
        should_pause_ai=getattr(state, "should_pause_ai", False),
        prompt_used=state.prompt_used[:10000] if state.prompt_used else None,  # Limitar tamanho
        model_used=state.model_used,
        tools_called=state.tools_called,
        latency_ms=state.latency_ms,
        tokens_used=state.tokens_used,
        error=state.error,
        metadata=state.metadata,
    )


async def _update_lead_state(state: AgentState) -> None:
    """Atualiza estado do lead no banco."""
    repo = LeadsRepository()

    update_data = {}

    # Log de debug para ver o estado
    logger.info(f"📊 Estado atual: {state.current_state.value}")
    logger.info(f"📊 Próximo estado: {state.next_state.value if state.next_state else 'None'}")

    # Atualizar estado se mudou
    if state.next_state and state.next_state != state.current_state:
        update_data["current_state"] = state.next_state.value
        logger.info(f"🔄 Atualizando estado de {state.current_state.value} para {state.next_state.value}")

    # Atualizar flags
    if state.no_money_flag:
        update_data["no_money_flag"] = True
        update_data["current_state"] = "NO_MONEY"

    if update_data:
        logger.info(f"💾 Salvando no banco: lead_id={state.lead_id}, update_data={update_data}")
        
        # Fazer update e verificar se funcionou
        result = await repo.update(state.lead_id, **update_data)
        
        if result:
            logger.info(f"✅ Lead {state.lead_id} atualizado com sucesso: {result.current_state.value}")
        else:
            logger.error(f"❌ FALHA ao atualizar lead {state.lead_id} - update retornou None!")
    else:
        logger.warning(f"⚠️ Nenhum update para lead {state.lead_id}")


async def _save_outbound_message(state: AgentState) -> None:
    """Salva mensagem de resposta."""
    repo = MessagesRepository()
    await repo.create_outbound_text(
        conversation_id=state.conversation_id,
        content=state.reply_text,
    )


async def _register_events(state: AgentState) -> None:
    """Registra eventos relevantes."""
    repo = EventsRepository()

    # Evento de mudança de estado
    if state.state_before != state.next_state:
        await repo.create(
            event_type=EventType.STATE_CHANGED,
            lead_id=state.lead_id,
            conversation_id=state.conversation_id,
            description=f"Estado mudou de {state.state_before.value if state.state_before else 'N/A'} para {state.next_state.value if state.next_state else 'N/A'}",
            metadata={
                "state_before": state.state_before.value if state.state_before else None,
                "state_after": state.next_state.value if state.next_state else None,
            },
        )

    # Evento de booking oferecido
    if state.should_call_booking_tool:
        await repo.create(
            event_type=EventType.BOOKING_CREATED,
            lead_id=state.lead_id,
            conversation_id=state.conversation_id,
            description="Booking oferecido ao lead",
            metadata={"offered": True},
        )

    # Evento de follow-up agendado
    if state.should_schedule_follow:
        await repo.create(
            event_type=EventType.FOLLOW_SCHEDULED,
            lead_id=state.lead_id,
            conversation_id=state.conversation_id,
            description="Follow-up agendado",
            metadata={"reason": state.follow_reason},
        )

    # P1-FIX: Evento de handoff para humano (pause AI)
    if getattr(state, "should_pause_ai", False):
        await repo.create(
            event_type=EventType.HANDOFF_TO_HUMAN,
            lead_id=state.lead_id,
            conversation_id=state.conversation_id,
            description="IA pausada — lead transferido para atendimento humano",
            metadata={
                "pause_reason": state.metadata.get("pause_reason", "LLM decided to pause"),
                "intent": state.metadata.get("intent", "UNKNOWN"),
            },
        )

    # P1-FIX: Evento de follow cancelado
    if "cancel_follow" in state.actions:
        await repo.create(
            event_type=EventType.FOLLOW_CANCELLED,
            lead_id=state.lead_id,
            conversation_id=state.conversation_id,
            description="Follow-up cancelado (lead respondeu ou estado mudou)",
            metadata={
                "reason": "Lead respondeu ativamente",
                "state": state.next_state.value if state.next_state else None,
            },
        )


async def _execute_state_actions(state: AgentState) -> None:
    """Executa ações de estado específicas."""
    leads_repo = LeadsRepository()

    # Marcar no_money
    if "mark_no_money" in state.actions:
        await leads_repo.mark_no_money(state.lead_id)
        logger.info("Lead marcado como NO_MONEY")

    # Marcar paused_by_human (via ação explícita)
    if "mark_paused_by_human" in state.actions:
        await leads_repo.mark_paused_by_human(state.lead_id)
        logger.info("Lead marcado como PAUSED_BY_HUMAN (via ação)")

    # Cancelar follow
    if "cancel_follow" in state.actions:
        from app.repositories.follow_jobs_repository import FollowJobsRepository
        follow_repo = FollowJobsRepository()
        await follow_repo.cancel_by_lead(state.lead_id, reason="Lead respondeu ativamente")
        logger.info("Follow-up cancelado")
