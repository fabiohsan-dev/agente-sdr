"""Serviço de outbound - envia mensagens e materiais."""

import logging
from uuid import UUID

from app.repositories.messages_repository import MessagesRepository

logger = logging.getLogger(__name__)


class OutboundService:
    """Serviço para envio de mensagens outbound."""

    def __init__(self):
        self.messages_repo = MessagesRepository()

    async def send_text_message(
        self,
        conversation_id: UUID,
        content: str,
    ) -> dict:
        """
        Envia mensagem de texto.

        Args:
            conversation_id: ID da conversation
            content: Conteúdo da mensagem

        Returns:
            Mensagem enviada
        """
        message = await self.messages_repo.create_outbound_text(
            conversation_id=conversation_id,
            content=content,
        )

        logger.debug(f"Mensagem outbound enviada: {message.id}")

        return {
            "message_id": str(message.id),
            "content": message.content,
            "sent_at": message.created_at.isoformat(),
        }

    async def send_materials(
        self,
        conversation_id: UUID,
        materials: list[dict],
    ) -> dict:
        """
        Envia materiais para o lead.

        Args:
            conversation_id: ID da conversation
            materials: Lista de materiais com url, title, description

        Returns:
            Resultado do envio
        """
        # Formatar mensagem com materiais
        content = self._format_materials_message(materials)

        message = await self.messages_repo.create_outbound_text(
            conversation_id=conversation_id,
            content=content,
        )

        logger.info(f"Materiais enviados: {len(materials)} itens")

        return {
            "message_id": str(message.id),
            "materials_count": len(materials),
            "sent_at": message.created_at.isoformat(),
        }

    async def send_checklist(
        self,
        conversation_id: UUID,
        checklist_items: list[str],
    ) -> dict:
        """
        Envia checklist para o lead.

        Args:
            conversation_id: ID da conversation
            checklist_items: Lista de itens do checklist

        Returns:
            Resultado do envio
        """
        # Formatar mensagem com checklist
        content = self._format_checklist_message(checklist_items)

        message = await self.messages_repo.create_outbound_text(
            conversation_id=conversation_id,
            content=content,
        )

        logger.info(f"Checklist enviado: {len(checklist_items)} itens")

        return {
            "message_id": str(message.id),
            "items_count": len(checklist_items),
            "sent_at": message.created_at.isoformat(),
        }

    def _format_materials_message(self, materials: list[dict]) -> str:
        """Formata mensagem de materiais."""
        lines = ["Ótimo! Preparei alguns materiais para você:\n"]

        for i, material in enumerate(materials, 1):
            title = material.get("title", f"Material {i}")
            description = material.get("description", "")
            url = material.get("url", "#")

            lines.append(f"{i}. **{title}**")
            if description:
                lines.append(f"   _{description}_")
            lines.append(f"   {url}\n")

        lines.append("\nDá uma olhada antes da nossa reunião! Qualquer dúvida, é só me chamar.")

        return "\n".join(lines)

    def _format_checklist_message(self, items: list[str]) -> str:
        """Formata mensagem de checklist."""
        lines = [
            "Preparei um checklist rápido para você antes da reunião:\n",
            "✅ **Checklist de Preparação**\n",
        ]

        for i, item in enumerate(items, 1):
            lines.append(f"{i}. [ ] {item}")

        lines.append(
            "\nConsegue me confirmar quando finalizar esses itens?\n"
            "Isso vai te ajudar a aproveitar ao máximo nossa reunião!"
        )

        return "\n".join(lines)

    async def _get_active_conversation_id(self, lead_id: UUID) -> UUID | None:
        """Busca a conversation ativa do lead."""
        from app.integrations.supabase.client import get_supabase_client

        client = get_supabase_client()
        result = (
            client.table("conversations")
            .select("id")
            .eq("lead_id", str(lead_id))
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            return UUID(result.data[0]["id"])
        return None

    async def send_text(self, lead_id: UUID, text: str) -> dict | None:
        """
        Envia texto para um lead via sua conversation ativa.
        Usado pelo follow-up worker.
        """
        conversation_id = await self._get_active_conversation_id(lead_id)
        if not conversation_id:
            logger.warning(f"Sem conversation ativa para lead {lead_id}")
            return None
        return await self.send_text_message(conversation_id, text)

    async def send_image(
        self, lead_id: UUID, image_url: str, caption: str | None = None
    ) -> dict | None:
        """
        Envia imagem para um lead via sua conversation ativa.
        Usado pelo follow-up worker.
        """
        conversation_id = await self._get_active_conversation_id(lead_id)
        if not conversation_id:
            logger.warning(f"Sem conversation ativa para lead {lead_id}")
            return None

        # Formatar como mensagem com URL de imagem
        content = f"[image:{image_url}]"
        if caption:
            content = f"{caption}\n{content}"

        return await self.send_text_message(conversation_id, content)


# Singleton
_outbound_service: OutboundService | None = None


def get_outbound_service() -> OutboundService:
    """Retorna instância singleton do OutboundService."""
    global _outbound_service
    if _outbound_service is None:
        _outbound_service = OutboundService()
    return _outbound_service
