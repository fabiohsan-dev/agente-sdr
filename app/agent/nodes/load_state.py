"""Node: load_state - Carrega estado do lead."""

import logging

from app.repositories.conversations_repository import ConversationsRepository
from app.repositories.leads_repository import LeadsRepository
from app.state.lead_states import AgentState

logger = logging.getLogger(__name__)


async def load_state(state: AgentState) -> AgentState:
    """
    Node de carregamento de estado.
    """
    logger.info("=" * 60)
    logger.info("🔍 LOAD_STATE - INICIANDO")
    logger.info(f"   state.lead_id: {state.lead_id}")
    logger.info(f"   state.session_id: {state.session_id}")
    logger.info("=" * 60)

    leads_repo = LeadsRepository()
    conversations_repo = ConversationsRepository()

    # ============================================
    # BUSCAR CONVERSATION PELA SESSION_ID (PRIORIDADE!)
    # ============================================

    conversation = None
    if state.session_id:
        logger.info(f"🔍 Buscando conversation por session_id: {state.session_id}")

        # Buscar conversation ativa mais recente com esta session_id
        try:
            result = (
                conversations_repo.client.table("conversations")
                .select("*")
                .eq("session_id", state.session_id)
                .eq("is_active", True)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            logger.info(
                f"   Resultado da busca: {len(result.data) if result.data else 0} conversations"
            )

            if result.data:
                conversation = conversations_repo._map_to_conversation(result.data[0])
                logger.info(f"✅ Conversation encontrada: {conversation.id}")
                logger.info(f"   Lead ID: {conversation.lead_id}")

                # Buscar lead associado a esta conversation
                if conversation.lead_id:
                    lead = await leads_repo.get_by_id(conversation.lead_id)
                    if lead:
                        logger.info(f"✅ Lead encontrado: {lead.id}")
                        logger.info(f"   Estado atual: {lead.current_state.value}")

                        state.update_from_lead(lead)
                        state.lead_id = lead.id
                        state.conversation_id = conversation.id

                        # Carregar mensagens recentes
                        recent_messages = await conversations_repo.get_recent_messages(
                            conversation_id=conversation.id,
                            limit=10,
                        )
                        state.recent_messages = recent_messages
                        state.conversation_context = _build_conversation_context(recent_messages)
                        logger.info(f"📜 Contexto carregado: {len(recent_messages)} mensagens")

                        # Atualizar system context e state_before
                        state.system_context = state.build_system_context()
                        state.mark_state_before()
                        logger.info("✅ ESTADO CARREGADO COM SUCESSO - USANDO SESSION_ID")
                        logger.info("=" * 60)
                        return state
                    else:
                        logger.error(f"❌ Lead {conversation.lead_id} não encontrado!")
                else:
                    logger.error("❌ Conversation sem lead_id!")
            else:
                logger.warning("⚠️ Nenhuma conversation encontrada")
        except Exception as e:
            logger.error(f"❌ ERRO ao buscar conversation: {e}")

    # ============================================
    # SE NÃO ENCONTROU PELA SESSION, BUSCAR PELO LEAD_ID
    # ============================================

    if state.lead_id:
        # Buscar lead existente por ID
        lead = await leads_repo.get_by_id(state.lead_id)
        if lead:
            state.update_from_lead(lead)
            state.lead_id = lead.id  # Garantir que lead_id está no estado
            logger.info(
                f"✅ Lead carregado por ID: {state.lead_id} (estado: {lead.current_state.value})"
            )
        else:
            state.error = f"Lead não encontrado: {state.lead_id}"
            logger.error(f"Lead não encontrado: {state.lead_id}")
            return state

    # ============================================
    # SE AINDA NÃO TEM LEAD, CRIAR NOVO (apenas quando nenhum lead_id foi fornecido)
    # ============================================

    if state.lead is None:
        # Criar lead novo (somente quando nenhum lead_id foi fornecido)
        logger.info("Nenhum lead encontrado, criando novo lead...")
        lead = await leads_repo.create(
            email=state.metadata.get("lead_email"),
            name=state.metadata.get("lead_name"),
            phone=state.metadata.get("lead_phone"),
            source=state.metadata.get("source", "playground"),
            tenant_id=state.tenant_id,
        )
        state.update_from_lead(lead)
        state.lead_id = lead.id
        logger.info(f"Novo lead criado: {state.lead_id}")

    # ============================================
    # CRIAR NOVA CONVERSATION
    # ============================================

    if state.lead_id and state.session_id:
        logger.info(
            f"💾 Criando nova conversation: lead_id={state.lead_id}, session_id={state.session_id}"
        )

        conversation = await conversations_repo.create(
            lead_id=state.lead_id,
            session_id=state.session_id,
            channel=state.metadata.get("channel", "playground"),
            metadata=state.metadata,
            tenant_id=state.tenant_id,
        )
        logger.info(f"✅ Conversation criada: {conversation.id}")
        logger.info(f"   Session ID: {conversation.session_id}")
        logger.info(f"   Lead ID: {conversation.lead_id}")

        state.conversation_id = conversation.id

        # Carregar mensagens recentes (vazio para nova conversation)
        recent_messages = await conversations_repo.get_recent_messages(
            conversation_id=conversation.id,
            limit=10,
        )
        state.recent_messages = recent_messages
        state.conversation_context = _build_conversation_context(recent_messages)
        logger.info(f"📜 Contexto carregado: {len(recent_messages)} mensagens")

    # ============================================
    # ATUALIZAR SISTEMA CONTEXT
    # ============================================

    state.system_context = state.build_system_context()
    state.mark_state_before()

    logger.debug("Carregamento de estado concluído")
    return state


def _build_conversation_context(messages: list[dict]) -> str:
    """Constrói contexto formatado da conversa."""
    if not messages:
        return ""

    context_lines = []
    for msg in reversed(messages[-10:]):  # Últimas 10 mensagens
        direction = "Usuário" if msg["direction"] == "inbound" else "Assistente"
        content = msg.get("content") or ""

        # Adicionar indicação de mídia
        if msg.get("media_type"):
            content += f" [{msg['media_type']}]"

        context_lines.append(f"{direction}: {content}")

    return "\n".join(reversed(context_lines))
