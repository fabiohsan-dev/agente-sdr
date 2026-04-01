"""Repositório de Messages."""

from datetime import datetime
from uuid import UUID

from supabase import Client

from app.domain.enums import MessageDirection, MessageType
from app.domain.message import Message
from app.integrations.supabase.client import get_supabase_client


class MessagesRepository:
    """Repositório para operações com Messages."""

    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()

    async def create(
        self,
        conversation_id: UUID,
        direction: MessageDirection,
        content: str | None = None,
        message_type: MessageType = MessageType.TEXT,
        media_url: str | None = None,
        media_mime_type: str | None = None,
        media_filename: str | None = None,
        media_transcription: str | None = None,
        media_analysis: str | None = None,
        metadata: dict | None = None,
    ) -> Message:
        """Cria uma nova mensagem."""
        data = {
            "conversation_id": str(conversation_id),
            "direction": direction.value,
            "message_type": message_type.value,
            "content": content,
            "media_url": media_url,
            "media_mime_type": media_mime_type,
            "media_filename": media_filename,
            "media_transcription": media_transcription,
            "media_analysis": media_analysis,
            "metadata": metadata or {},
        }

        result = self.client.table("messages").insert(data).execute()
        return self._map_to_message(result.data[0])

    async def create_inbound_text(
        self,
        conversation_id: UUID,
        content: str,
    ) -> Message:
        """Cria mensagem inbound de texto."""
        return await self.create(
            conversation_id=conversation_id,
            direction=MessageDirection.INBOUND,
            content=content,
            message_type=MessageType.TEXT,
        )

    async def create_outbound_text(
        self,
        conversation_id: UUID,
        content: str,
    ) -> Message:
        """Cria mensagem outbound de texto."""
        return await self.create(
            conversation_id=conversation_id,
            direction=MessageDirection.OUTBOUND,
            content=content,
            message_type=MessageType.TEXT,
        )

    async def create_inbound_media(
        self,
        conversation_id: UUID,
        media_url: str,
        media_type: MessageType,
        media_mime_type: str | None = None,
        media_filename: str | None = None,
        transcription: str | None = None,
        analysis: str | None = None,
    ) -> Message:
        """Cria mensagem inbound de mídia."""
        return await self.create(
            conversation_id=conversation_id,
            direction=MessageDirection.INBOUND,
            message_type=media_type,
            media_url=media_url,
            media_mime_type=media_mime_type,
            media_filename=media_filename,
            media_transcription=transcription,
            media_analysis=analysis,
        )

    async def get_by_conversation(self, conversation_id: UUID, limit: int = 50) -> list[Message]:
        """Busca mensagens de uma conversation."""
        result = (
            self.client.table("messages")
            .select("*")
            .eq("conversation_id", str(conversation_id))
            .order("created_at", asc=True)
            .limit(limit)
            .execute()
        )

        return [self._map_to_message(m) for m in result.data or []]

    async def get_by_id(self, message_id: UUID) -> Message | None:
        """Busca mensagem por ID."""
        result = self.client.table("messages").select("*").eq("id", str(message_id)).execute()

        if not result.data:
            return None
        return self._map_to_message(result.data[0])

    def _map_to_message(self, data: dict) -> Message:
        """Mapeia dados do Supabase para Message."""
        return Message(
            id=UUID(data["id"]),
            conversation_id=UUID(data["conversation_id"]),
            message_type=MessageType(data["message_type"]),
            direction=MessageDirection(data["direction"]),
            content=data.get("content"),
            media_url=data.get("media_url"),
            media_mime_type=data.get("media_mime_type"),
            media_filename=data.get("media_filename"),
            media_transcription=data.get("media_transcription"),
            media_analysis=data.get("media_analysis"),
            metadata=data.get("metadata") or {},
            created_at=datetime.fromisoformat(data["created_at"]),
        )
