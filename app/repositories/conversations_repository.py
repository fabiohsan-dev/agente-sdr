"""Repositório de Conversations."""

from datetime import datetime
from uuid import UUID

from supabase import Client

from app.domain.conversation import Conversation
from app.integrations.supabase.client import get_supabase_client


class ConversationsRepository:
    """Repositório para operações com Conversations."""

    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()

    async def create(
        self,
        lead_id: UUID,
        session_id: str,
        channel: str | None = None,
        metadata: dict | None = None,
        tenant_id: UUID | None = None,
    ) -> Conversation:
        """Cria uma nova conversation."""
        data = {
            "lead_id": str(lead_id),
            "session_id": session_id,
            "channel": channel,
            "metadata": metadata or {},
            "is_active": True,
        }
        if tenant_id:
            data["tenant_id"] = str(tenant_id)

        result = (
            self.client.table("conversations")
            .insert(data)
            .execute()
        )
        return self._map_to_conversation(result.data[0])

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        """Busca conversation por ID."""
        result = (
            self.client.table("conversations")
            .select("*")
            .eq("id", str(conversation_id))
            .execute()
        )

        if not result.data:
            return None
        return self._map_to_conversation(result.data[0])

    async def get_by_session_id(
        self, session_id: str, lead_id: UUID
    ) -> Conversation | None:
        """Busca conversation por session_id e lead_id."""
        result = (
            self.client.table("conversations")
            .select("*")
            .eq("session_id", session_id)
            .eq("lead_id", str(lead_id))
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not result.data:
            return None
        return self._map_to_conversation(result.data[0])

    async def get_active_by_lead(
        self, lead_id: UUID
    ) -> Conversation | None:
        """Busca conversation ativa por lead."""
        result = (
            self.client.table("conversations")
            .select("*")
            .eq("lead_id", str(lead_id))
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not result.data:
            return None
        return self._map_to_conversation(result.data[0])

    async def deactivate(self, conversation_id: UUID) -> None:
        """Desativa uma conversation."""
        self.client.table("conversations").update(
            {"is_active": False}
        ).eq("id", str(conversation_id)).execute()

    async def get_recent_messages(
        self, conversation_id: UUID, limit: int = 10
    ) -> list[dict]:
        """Busca mensagens recentes de uma conversation."""
        result = (
            self.client.table("messages")
            .select("*")
            .eq("conversation_id", str(conversation_id))
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return result.data or []

    def _map_to_conversation(self, data: dict) -> Conversation:
        """Mapeia dados do Supabase para Conversation."""
        return Conversation(
            id=UUID(data["id"]),
            lead_id=UUID(data["lead_id"]),
            session_id=data["session_id"],
            is_active=data["is_active"],
            channel=data.get("channel"),
            metadata=data.get("metadata") or {},
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            last_message_at=(
                datetime.fromisoformat(data["last_message_at"])
                if data.get("last_message_at")
                else None
            ),
        )
