"""Serviço de contexto - constrói contexto para o agente."""

import logging

from app.repositories.conversations_repository import ConversationsRepository
from app.repositories.leads_repository import LeadsRepository

logger = logging.getLogger(__name__)


class ContextService:
    """Serviço para construção de contexto para o agente."""

    def __init__(self):
        self.leads_repo = LeadsRepository()
        self.conversations_repo = ConversationsRepository()

    async def build_conversation_context(
        self,
        conversation_id: str,
        limit: int = 20,
    ) -> str:
        """
        Constrói contexto da conversa para o agente.

        Args:
            conversation_id: ID da conversation
            limit: Número máximo de mensagens

        Returns:
            Contexto formatado da conversa
        """
        from uuid import UUID

        try:
            conv_id = UUID(conversation_id)
        except ValueError:
            logger.warning(f"Conversation ID inválido: {conversation_id}")
            return ""

        messages = await self.conversations_repo.get_recent_messages(
            conversation_id=conv_id,
            limit=limit,
        )

        if not messages:
            return "[Sem histórico de conversa]"

        context_lines = []
        for msg in messages:
            direction = "Usuário" if msg["direction"] == "inbound" else "Assistente"
            content = msg.get("content") or ""

            # Adicionar indicação de mídia
            if msg.get("media_type"):
                content += f" [{msg['media_type']}]"

            context_lines.append(f"{direction}: {content}")

        return "\n".join(context_lines)

    async def build_lead_context(
        self,
        lead_id: str,
    ) -> dict:
        """
        Constrói contexto do lead para o agente.

        Args:
            lead_id: ID do lead

        Returns:
            Dict com contexto do lead
        """
        from uuid import UUID

        try:
            lid = UUID(lead_id)
        except ValueError:
            logger.warning(f"Lead ID inválido: {lead_id}")
            return {}

        lead = await self.leads_repo.get_by_id(lid)
        if not lead:
            return {}

        return {
            "lead_id": str(lead.id),
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
            "current_state": lead.current_state.value,
            "owner_mode": lead.owner_mode.value,
            "has_booking": lead.has_booking,
            "no_money_flag": lead.no_money_flag,
        }

    async def build_full_context(
        self,
        lead_id: str,
        conversation_id: str,
    ) -> dict:
        """
        Constrói contexto completo para o agente.

        Args:
            lead_id: ID do lead
            conversation_id: ID da conversation

        Returns:
            Dict com contexto completo
        """
        lead_context = await self.build_lead_context(lead_id)
        conversation_context = await self.build_conversation_context(conversation_id)

        return {
            "lead": lead_context,
            "conversation_history": conversation_context,
            "system_context": {
                "current_state": lead_context.get("current_state", "NEW"),
                "owner_mode": lead_context.get("owner_mode", "agent"),
                "has_booking": lead_context.get("has_booking", False),
                "no_money_flag": lead_context.get("no_money_flag", False),
            },
        }


# Singleton
_context_service: ContextService | None = None


def get_context_service() -> ContextService:
    """Retorna instância singleton do ContextService."""
    global _context_service
    if _context_service is None:
        _context_service = ContextService()
    return _context_service
