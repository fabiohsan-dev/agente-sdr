"""Repositório de Follow Jobs."""

from datetime import datetime
from uuid import UUID

from supabase import Client

from app.domain.enums import FollowJobStatus
from app.integrations.supabase.client import get_supabase_client


class FollowJobsRepository:
    """Repositório para operações com Follow Jobs."""

    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()

    async def create(
        self,
        lead_id: UUID,
        scheduled_for: datetime,
        reason: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Cria um novo follow job."""
        data = {
            "lead_id": str(lead_id),
            "scheduled_for": scheduled_for.isoformat(),
            "reason": reason,
            "metadata": metadata or {},
            "status": FollowJobStatus.PENDING.value,
        }

        result = self.client.table("follow_jobs").insert(data).execute()
        return result.data[0]

    async def get_pending_by_lead(self, lead_id: UUID) -> dict | None:
        """Busca follow job pendente de um lead."""
        result = (
            self.client.table("follow_jobs")
            .select("*")
            .eq("lead_id", str(lead_id))
            .eq("status", FollowJobStatus.PENDING.value)
            .order("scheduled_for", asc=True)
            .limit(1)
            .execute()
        )

        if not result.data:
            return None
        return result.data[0]

    async def complete(self, job_id: UUID) -> dict | None:
        """Marca follow job como completado."""
        result = (
            self.client.table("follow_jobs")
            .update(
                {
                    "status": FollowJobStatus.COMPLETED.value,
                    "completed_at": datetime.utcnow().isoformat(),
                }
            )
            .eq("id", str(job_id))
            .execute()
        )

        if not result.data:
            return None
        return result.data[0]

    async def cancel(self, job_id: UUID, reason: str | None = None) -> dict | None:
        """Cancela follow job."""
        update_data = {
            "status": FollowJobStatus.CANCELLED.value,
            "cancelled_at": datetime.utcnow().isoformat(),
        }
        if reason:
            update_data["metadata"] = {"cancel_reason": reason}

        result = (
            self.client.table("follow_jobs").update(update_data).eq("id", str(job_id)).execute()
        )

        if not result.data:
            return None
        return result.data[0]

    async def cancel_by_lead(self, lead_id: UUID, reason: str | None = None) -> None:
        """Cancela todos follow jobs pendentes de um lead."""
        update_data = {
            "status": FollowJobStatus.CANCELLED.value,
            "cancelled_at": datetime.utcnow().isoformat(),
        }
        if reason:
            update_data["metadata"] = {"cancel_reason": reason}

        self.client.table("follow_jobs").update(update_data).eq("lead_id", str(lead_id)).eq(
            "status", FollowJobStatus.PENDING.value
        ).execute()

    async def get_overdue(self, limit: int = 100) -> list[dict]:
        """Busca follow jobs vencidos (scheduled_for <= NOW, status = pending).

        Usada pelo worker de follow-up para encontrar jobs prontos para execução.

        Returns:
            Lista de follow jobs vencidos, ordenados pelo mais antigo primeiro.
        """
        now = datetime.utcnow().isoformat()
        result = (
            self.client.table("follow_jobs")
            .select("*")
            .eq("status", FollowJobStatus.PENDING.value)
            .lte("scheduled_for", now)
            .order("scheduled_for", desc=False)
            .limit(limit)
            .execute()
        )
        return result.data or []

    async def mark_failed(self, job_id: UUID, error: str | None = None) -> dict | None:
        """Marca follow job como failed."""
        update_data = {
            "status": FollowJobStatus.FAILED.value,
            "completed_at": datetime.utcnow().isoformat(),
        }
        if error:
            update_data["metadata"] = {"error": error}

        result = (
            self.client.table("follow_jobs").update(update_data).eq("id", str(job_id)).execute()
        )

        if not result.data:
            return None
        return result.data[0]
