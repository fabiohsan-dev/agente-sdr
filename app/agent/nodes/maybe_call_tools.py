"""Node: maybe_call_tools - Chama tools se necessário."""

import logging
from datetime import datetime, timedelta

from app.state.lead_states import AgentState

logger = logging.getLogger(__name__)


async def maybe_call_tools(state: AgentState) -> AgentState:
    """
    Node de chamada de tools.

    Responsabilidades:
    - Chamar serviço de booking se should_call_booking_tool (Cal.com REAL)
    - Chamar serviço de follow-up se should_schedule_follow
    - Chamar serviço de materiais se should_send_materials
    - Chamar serviço de checklist se should_send_checklist
    - Registrar tools chamadas no metadata
    """
    logger.debug("Verificando chamada de tools")

    tools_called = []

    # ============================================
    # BOOKING TOOL — Cal.com real
    # ============================================

    if state.should_call_booking_tool:
        logger.info("📅 Chamando booking tool (Cal.com)")
        try:
            from app.services.booking_service import get_booking_service

            booking_service = get_booking_service()

            # Extrair dados do lead do metadata (acumulados nas etapas anteriores)
            lead_name = state.metadata.get("lead_name") or "Lead"
            lead_email = state.metadata.get("lead_email") or state.metadata.get("email_provided")
            scheduled_time_str = state.metadata.get("scheduled_time")

            # Determinar o horário do booking
            if scheduled_time_str:
                try:
                    start_time = datetime.fromisoformat(scheduled_time_str)
                except ValueError:
                    start_time = datetime.now() + timedelta(days=1)
                    start_time = start_time.replace(hour=14, minute=0, second=0, microsecond=0)
            else:
                # Sem horário definido: agendar para amanhã às 14h BRT
                start_time = datetime.now() + timedelta(days=1)
                start_time = start_time.replace(hour=14, minute=0, second=0, microsecond=0)

            end_time = start_time + timedelta(minutes=45)

            if lead_email and state.lead_id:
                booking = await booking_service.create_booking(
                    lead_id=state.lead_id,
                    start_time=start_time,
                    end_time=end_time,
                    name=lead_name,
                    email=lead_email,
                    timezone="America/Sao_Paulo",
                    title=f"Reunião SDR - {lead_name}",
                    description=(
                        f"Reunião agendada automaticamente pelo agente SDR. "
                        f"Lead ID: {state.lead_id}"
                    ),
                )

                if booking:
                    state.metadata["booking_id"] = str(booking.id)
                    state.metadata["booking_confirmed"] = True
                    state.metadata["meeting_url"] = booking.meeting_url
                    state.metadata["booking_start"] = start_time.isoformat()
                    logger.info(
                        f"✅ Booking criado: {booking.id} | Cal.com ID: {booking.calcom_booking_id}"
                    )
                    tools_called.append(
                        {
                            "tool": "booking_tool",
                            "action": "create_booking",
                            "status": "success",
                            "booking_id": str(booking.id),
                        }
                    )
                else:
                    logger.warning("⚠️ Booking não criado (sem retorno do serviço)")
                    tools_called.append(
                        {
                            "tool": "booking_tool",
                            "action": "create_booking",
                            "status": "failed",
                        }
                    )
            else:
                logger.warning(f"⚠️ Booking não criado: email={lead_email}, lead_id={state.lead_id}")
                tools_called.append(
                    {
                        "tool": "booking_tool",
                        "action": "create_booking",
                        "status": "skipped_missing_data",
                        "reason": f"email={lead_email}",
                    }
                )

        except Exception as e:
            logger.error(f"❌ Erro ao criar booking: {type(e).__name__}: {e}")
            tools_called.append(
                {
                    "tool": "booking_tool",
                    "action": "create_booking",
                    "status": "error",
                    "error": str(e),
                }
            )

    # ============================================
    # FOLLOW-UP TOOL — Cadência de 4 passos
    # ============================================

    if state.should_schedule_follow:
        logger.info("📩 Agendando follow-up (cadência)")
        try:
            from app.repositories.leads_repository import LeadsRepository
            from app.services.follow_up_service import get_follow_up_service

            follow_service = get_follow_up_service()
            leads_repo = LeadsRepository()

            # P0-FIX: Ler follow_step do BANCO (não do metadata efêmero)
            current_step = 0
            if state.lead_id:
                lead = await leads_repo.get_by_id(state.lead_id)
                if lead:
                    current_step = lead.follow_step
                    logger.info(f"📩 Follow step atual (do banco): {current_step}/4")

            # Nome do lead para personalização das mensagens
            first_name = (
                state.metadata.get("lead_name", "").split()[0]
                if state.metadata.get("lead_name")
                else ""
            )

            if state.lead_id:
                follow_job = await follow_service.schedule_follow_sequence(
                    lead_id=state.lead_id,
                    first_name=first_name,
                    current_follow_step=current_step,
                    reason=state.follow_reason,
                )

                if follow_job:
                    next_step = current_step + 1
                    # P0-FIX: Persistir follow_step no BANCO
                    await leads_repo.update_follow_step(state.lead_id, next_step)
                    state.metadata["follow_step"] = next_step
                    state.metadata["follow_job_id"] = follow_job.get("id")
                    logger.info(f"✅ Follow {next_step}/4 agendado (step salvo no banco)")
                    tools_called.append(
                        {
                            "tool": "follow_up_tool",
                            "action": "schedule_follow",
                            "step": next_step,
                            "status": "success",
                        }
                    )
                else:
                    logger.info("📩 Cadência de follow finalizada (4/4 já enviados)")
                    tools_called.append(
                        {
                            "tool": "follow_up_tool",
                            "action": "schedule_follow",
                            "status": "cadence_complete",
                        }
                    )
            else:
                logger.warning("⚠️ Follow-up não agendado: lead_id ausente")
                tools_called.append(
                    {
                        "tool": "follow_up_tool",
                        "action": "schedule_follow",
                        "status": "skipped_no_lead_id",
                    }
                )

        except Exception as e:
            logger.error(f"❌ Erro ao agendar follow-up: {type(e).__name__}: {e}")
            tools_called.append(
                {
                    "tool": "follow_up_tool",
                    "action": "schedule_follow",
                    "status": "error",
                    "error": str(e),
                }
            )

    # ============================================
    # MATERIALS TOOL
    # ============================================

    if state.should_send_materials:
        logger.info("Materials tool será chamada")
        # TODO: Implementar chamada real
        # result = await outbound_service.send_materials(...)
        tools_called.append(
            {
                "tool": "materials_tool",
                "action": "send_materials",
                "status": "pending_implementation",
            }
        )

    # ============================================
    # CHECKLIST TOOL
    # ============================================

    if state.should_send_checklist:
        logger.info("Checklist tool será chamada")
        # TODO: Implementar chamada real
        # result = await outbound_service.send_checklist(...)
        tools_called.append(
            {
                "tool": "checklist_tool",
                "action": "send_checklist",
                "status": "pending_implementation",
            }
        )

    # ============================================
    # PAUSE AI TOOL — TOOL 5 (Pausar IA)
    # ============================================
    # Cenários:
    #   A) Lead recusa mesmo após tratamento de objeção
    #   B) Lead diz que não tem condições financeiras
    #   C) Lead demonstra resistência ao bot / pede humano
    #   D) Lead encerrou elegantemente
    # Ordem: LLM responde (reply_text) → marca pause → cancela follows

    if getattr(state, "should_pause_ai", False):
        logger.info("⏸️ Pausar IA acionada pelo LLM")
        try:
            from app.domain.enums import LeadState
            from app.repositories.leads_repository import LeadsRepository

            # 1. Marcar lead como PAUSED_BY_HUMAN no banco
            if state.lead_id:
                leads_repo = LeadsRepository()
                await leads_repo.mark_paused_by_human(state.lead_id)
                logger.info(f"✅ Lead {state.lead_id} marcado como PAUSED_BY_HUMAN")

            # 2. Forçar next_state para PAUSED_BY_HUMAN
            state.next_state = LeadState.PAUSED_BY_HUMAN

            # 3. Cancelar follow-ups pendentes (evitar bot enviar msgs)
            from app.services.follow_up_service import get_follow_up_service

            follow_service = get_follow_up_service()
            if state.lead_id:
                cancelled = await follow_service.cancel_pending_follows(
                    lead_id=state.lead_id,
                    reason="Pausar IA acionada — lead desqualificado ou pediu encerramento",
                )
                if cancelled:
                    logger.info(f"🚫 {cancelled} follow(s) cancelado(s) pela Pausar IA")

            # 4. Desabilitar qualquer agendamento pendente
            state.should_schedule_follow = False
            state.should_call_booking_tool = False

            tools_called.append(
                {
                    "tool": "pause_ai_tool",
                    "action": "pause_ai",
                    "status": "success",
                    "reason": state.metadata.get("pause_reason", "LLM decided to pause"),
                }
            )

        except Exception as e:
            logger.error(f"❌ Erro ao pausar IA: {type(e).__name__}: {e}")
            tools_called.append(
                {
                    "tool": "pause_ai_tool",
                    "action": "pause_ai",
                    "status": "error",
                    "error": str(e),
                }
            )

    # ============================================
    # CANCEL FOLLOW (ação — quando lead responde)
    # ============================================

    if "cancel_follow" in state.actions:
        logger.info("🚫 Cancelando follow-up pendente (lead respondeu)")
        try:
            from app.repositories.leads_repository import LeadsRepository
            from app.services.follow_up_service import get_follow_up_service

            follow_service = get_follow_up_service()

            if state.lead_id:
                cancelled = await follow_service.cancel_pending_follows(
                    lead_id=state.lead_id,
                    reason="Lead respondeu ativamente",
                )
                # P0-FIX: Reset do step persistido no BANCO
                leads_repo = LeadsRepository()
                await leads_repo.reset_follow_step(state.lead_id)
                state.metadata["follow_step"] = 0
                tools_called.append(
                    {
                        "tool": "follow_up_tool",
                        "action": "cancel_follow",
                        "cancelled": cancelled,
                        "status": "success",
                    }
                )
            else:
                tools_called.append(
                    {
                        "tool": "follow_up_tool",
                        "action": "cancel_follow",
                        "status": "skipped_no_lead_id",
                    }
                )

        except Exception as e:
            logger.error(f"❌ Erro ao cancelar follow: {e}")
            tools_called.append(
                {
                    "tool": "follow_up_tool",
                    "action": "cancel_follow",
                    "status": "error",
                    "error": str(e),
                }
            )

    # ============================================
    # MARK NO_MONEY (ação)
    # ============================================

    if "mark_no_money" in state.actions:
        logger.info("Marcando lead como NO_MONEY")
        # Isso será feito no node persist_decision
        tools_called.append(
            {
                "tool": "lead_repository",
                "action": "mark_no_money",
                "status": "will_persist",
            }
        )

    state.tools_called = tools_called
    state.metadata["tools_executed"] = len(tools_called) > 0

    logger.debug(f"Tools verificadas: {len(tools_called)} chamadas")
    return state
