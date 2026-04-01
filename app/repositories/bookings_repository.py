"""Repositório de Bookings."""

from datetime import datetime
from uuid import UUID

from supabase import Client

from app.domain.booking import Booking
from app.integrations.supabase.client import get_supabase_client


class BookingsRepository:
    """Repositório para operações com Bookings."""

    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()

    async def create(
        self,
        lead_id: UUID,
        start_time: datetime,
        end_time: datetime,
        timezone: str = "America/Sao_Paulo",
        title: str | None = None,
        description: str | None = None,
        calcom_booking_id: int | None = None,
        meeting_url: str | None = None,
        calcom_data: dict | None = None,
        status: str = "confirmed",
    ) -> Booking:
        """Cria um novo booking."""
        data = {
            "lead_id": str(lead_id),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "timezone": timezone,
            "title": title,
            "description": description,
            "calcom_booking_id": calcom_booking_id,
            "meeting_url": meeting_url,
            "calcom_data": calcom_data or {},
            "status": status,
        }

        result = self.client.table("bookings").insert(data).execute()
        return self._map_to_booking(result.data[0])

    async def get_by_id(self, booking_id: UUID) -> Booking | None:
        """Busca booking por ID."""
        result = self.client.table("bookings").select("*").eq("id", str(booking_id)).execute()

        if not result.data:
            return None
        return self._map_to_booking(result.data[0])

    async def get_by_calcom_id(self, calcom_booking_id: int) -> Booking | None:
        """Busca booking por ID do Cal.com."""
        result = (
            self.client.table("bookings")
            .select("*")
            .eq("calcom_booking_id", calcom_booking_id)
            .execute()
        )

        if not result.data:
            return None
        return self._map_to_booking(result.data[0])

    async def get_by_lead(self, lead_id: UUID) -> list[Booking]:
        """Busca bookings de um lead."""
        result = (
            self.client.table("bookings")
            .select("*")
            .eq("lead_id", str(lead_id))
            .order("start_time", desc=True)
            .execute()
        )

        return [self._map_to_booking(b) for b in result.data or []]

    async def get_active_by_lead(self, lead_id: UUID) -> Booking | None:
        """Busca booking ativo de um lead."""
        result = (
            self.client.table("bookings")
            .select("*")
            .eq("lead_id", str(lead_id))
            .eq("status", "confirmed")
            .order("start_time", desc=False)  # asc=True não funciona, usar desc=False
            .limit(1)
            .execute()
        )

        if not result.data:
            return None
        return self._map_to_booking(result.data[0])

    async def update_status(self, booking_id: UUID, status: str) -> Booking | None:
        """Atualiza status do booking."""
        result = (
            self.client.table("bookings")
            .update({"status": status})
            .eq("id", str(booking_id))
            .execute()
        )

        if not result.data:
            return None
        return self._map_to_booking(result.data[0])

    async def cancel(self, booking_id: UUID, reason: str | None = None) -> Booking | None:
        """Cancela um booking."""
        result = (
            self.client.table("bookings")
            .update(
                {
                    "status": "cancelled",
                    "cancelled_at": datetime.utcnow().isoformat(),
                }
            )
            .eq("id", str(booking_id))
            .execute()
        )

        if not result.data:
            return None
        return self._map_to_booking(result.data[0])

    def _map_to_booking(self, data: dict) -> Booking:
        """Mapeia dados do Supabase para Booking."""
        return Booking(
            id=UUID(data["id"]),
            lead_id=UUID(data["lead_id"]),
            calcom_booking_id=data.get("calcom_booking_id"),
            title=data.get("title"),
            description=data.get("description"),
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            timezone=data.get("timezone", "America/Sao_Paulo"),
            status=data.get("status", "confirmed"),
            cancelled_at=(
                datetime.fromisoformat(data["cancelled_at"]) if data.get("cancelled_at") else None
            ),
            rescheduled_from_id=(
                UUID(data["rescheduled_from_id"]) if data.get("rescheduled_from_id") else None
            ),
            meeting_url=data.get("meeting_url"),
            calcom_data=data.get("calcom_data") or {},
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
