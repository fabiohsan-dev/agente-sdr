"""Repositório de Media Assets."""

from datetime import datetime
from uuid import UUID

from supabase import Client

from app.domain.enums import MediaType, MediaStatus
from app.integrations.supabase.client import get_supabase_client


class MediaAssetsRepository:
    """Repositório para operações com Media Assets."""

    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()

    async def create(
        self,
        lead_id: UUID,
        media_type: MediaType,
        cdn_url: str,
        conversation_id: UUID | None = None,
        message_id: UUID | None = None,
        mime_type: str | None = None,
        original_filename: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Cria um novo media asset."""
        data = {
            "lead_id": str(lead_id),
            "conversation_id": str(conversation_id) if conversation_id else None,
            "message_id": str(message_id) if message_id else None,
            "media_type": media_type.value,
            "cdn_url": cdn_url,
            "mime_type": mime_type,
            "original_filename": original_filename,
            "status": MediaStatus.PENDING.value,
            "metadata": metadata or {},
        }

        result = (
            self.client.table("media_assets")
            .insert(data)
            .execute()
        )
        return result.data[0]

    async def get_by_id(self, asset_id: UUID) -> dict | None:
        """Busca media asset por ID."""
        result = (
            self.client.table("media_assets")
            .select("*")
            .eq("id", str(asset_id))
            .execute()
        )

        if not result.data:
            return None
        return result.data[0]

    async def get_by_lead(self, lead_id: UUID) -> list[dict]:
        """Busca media assets de um lead."""
        result = (
            self.client.table("media_assets")
            .select("*")
            .eq("lead_id", str(lead_id))
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def get_by_message(self, message_id: UUID) -> dict | None:
        """Busca media asset por message_id."""
        result = (
            self.client.table("media_assets")
            .select("*")
            .eq("message_id", str(message_id))
            .execute()
        )

        if not result.data:
            return None
        return result.data[0]

    async def update_status(
        self,
        asset_id: UUID,
        status: MediaStatus,
        transcription: str | None = None,
        analysis: str | None = None,
    ) -> dict | None:
        """Atualiza status e dados de processamento do media asset."""
        update_data = {
            "status": status.value,
            "processed_at": datetime.utcnow().isoformat(),
        }
        if transcription:
            update_data["transcription"] = transcription
        if analysis:
            update_data["analysis"] = analysis

        result = (
            self.client.table("media_assets")
            .update(update_data)
            .eq("id", str(asset_id))
            .execute()
        )

        if not result.data:
            return None
        return result.data[0]

    async def mark_completed(
        self,
        asset_id: UUID,
        transcription: str | None = None,
        analysis: str | None = None,
    ) -> dict | None:
        """Marca media asset como completado."""
        return await self.update_status(
            asset_id,
            MediaStatus.COMPLETED,
            transcription,
            analysis,
        )

    async def mark_failed(self, asset_id: UUID, error: str) -> dict | None:
        """Marca media asset como falhou."""
        result = (
            self.client.table("media_assets")
            .update(
                {
                    "status": MediaStatus.FAILED.value,
                    "metadata": {"error": error},
                }
            )
            .eq("id", str(asset_id))
            .execute()
        )

        if not result.data:
            return None
        return result.data[0]
