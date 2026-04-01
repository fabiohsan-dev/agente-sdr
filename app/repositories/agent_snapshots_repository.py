"""Repositório de Agent Snapshots."""

from datetime import datetime
from uuid import UUID

from supabase import Client

from app.domain.enums import LeadState
from app.integrations.supabase.client import get_supabase_client


class AgentSnapshotsRepository:
    """Repositório para operações com Agent Snapshots."""

    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()

    async def create(
        self,
        lead_id: UUID,
        conversation_id: UUID | None = None,
        state_before: LeadState | None = None,
        state_after: LeadState | None = None,
        reply_text: str | None = None,
        actions: list[str] | None = None,
        should_schedule_follow: bool = False,
        should_call_booking_tool: bool = False,
        should_send_materials: bool = False,
        should_send_checklist: bool = False,
        should_pause_ai: bool = False,
        prompt_used: str | None = None,
        model_used: str | None = None,
        tools_called: list | None = None,
        latency_ms: int | None = None,
        tokens_used: int | None = None,
        error: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Cria um novo agent snapshot."""
        data = {
            "lead_id": str(lead_id),
            "conversation_id": str(conversation_id) if conversation_id else None,
            "state_before": state_before.value if state_before else None,
            "state_after": state_after.value if state_after else None,
            "reply_text": reply_text,
            "actions": actions or [],
            "should_schedule_follow": should_schedule_follow,
            "should_call_booking_tool": should_call_booking_tool,
            "should_send_materials": should_send_materials,
            "should_send_checklist": should_send_checklist,
            "should_pause_ai": should_pause_ai,
            "prompt_used": prompt_used,
            "model_used": model_used,
            "tools_called": tools_called or [],
            "latency_ms": latency_ms,
            "tokens_used": tokens_used,
            "error": error,
            "metadata": metadata or {},
        }

        result = (
            self.client.table("agent_snapshots")
            .insert(data)
            .execute()
        )
        return result.data[0]

    async def get_by_lead(
        self, lead_id: UUID, limit: int = 50
    ) -> list[dict]:
        """Busca snapshots de um lead."""
        result = (
            self.client.table("agent_snapshots")
            .select("*")
            .eq("lead_id", str(lead_id))
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    async def get_by_conversation(
        self, conversation_id: UUID, limit: int = 50
    ) -> list[dict]:
        """Busca snapshots de uma conversation."""
        result = (
            self.client.table("agent_snapshots")
            .select("*")
            .eq("conversation_id", str(conversation_id))
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    async def get_with_errors(
        self, limit: int = 100
    ) -> list[dict]:
        """Busca snapshots com erros."""
        result = (
            self.client.table("agent_snapshots")
            .select("*")
            .not_("error", "is", None)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
