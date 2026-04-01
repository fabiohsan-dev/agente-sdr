"""Repositório de Events."""

from uuid import UUID

from supabase import Client

from app.domain.enums import EventType
from app.integrations.supabase.client import get_supabase_client


class EventsRepository:
    """Repositório para operações com Events."""

    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()

    async def create(
        self,
        event_type: EventType,
        lead_id: UUID | None = None,
        conversation_id: UUID | None = None,
        description: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Cria um novo event."""
        data = {
            "lead_id": str(lead_id) if lead_id else None,
            "conversation_id": str(conversation_id) if conversation_id else None,
            "event_type": event_type.value,
            "description": description,
            "metadata": metadata or {},
        }

        result = self.client.table("events").insert(data).execute()
        return result.data[0]

    async def get_by_lead(self, lead_id: UUID, limit: int = 100) -> list[dict]:
        """Busca eventos de um lead."""
        result = (
            self.client.table("events")
            .select("*")
            .eq("lead_id", str(lead_id))
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    async def get_by_conversation(self, conversation_id: UUID, limit: int = 100) -> list[dict]:
        """Busca eventos de uma conversation."""
        result = (
            self.client.table("events")
            .select("*")
            .eq("conversation_id", str(conversation_id))
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
