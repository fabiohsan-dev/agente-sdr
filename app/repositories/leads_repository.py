"""Repositório de Leads."""

from datetime import datetime
from uuid import UUID

from supabase import Client

from app.domain.enums import LeadState, OwnerMode
from app.domain.lead import Lead
from app.integrations.supabase.client import get_supabase_client


class LeadsRepository:
    """Repositório para operações com Leads."""

    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()

    async def create(
        self,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        company: str | None = None,
        source: str | None = None,
        tenant_id: UUID | None = None,
    ) -> Lead:
        """Cria um novo lead."""
        data = {
            "name": name,
            "email": email,
            "phone": phone,
            "company": company,
            "source": source,
            "current_state": LeadState.NEW.value,
            "owner_mode": OwnerMode.AGENT.value,
        }
        if tenant_id:
            data["tenant_id"] = str(tenant_id)

        result = self.client.table("leads").insert(data).execute()
        return self._map_to_lead(result.data[0])

    async def get_by_id(self, lead_id: UUID) -> Lead | None:
        """Busca lead por ID."""
        result = self.client.table("leads").select("*").eq("id", str(lead_id)).execute()

        if not result.data:
            return None
        return self._map_to_lead(result.data[0])

    async def get_by_email(
        self,
        email: str,
        tenant_id: UUID | None = None,
    ) -> Lead | None:
        """Busca lead por email (scoped ao tenant se fornecido)."""
        query = self.client.table("leads").select("*").eq("email", email)
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        result = query.execute()

        if not result.data:
            return None
        return self._map_to_lead(result.data[0])

    async def get_by_phone(self, phone: str) -> Lead | None:
        """Busca lead por phone."""
        result = self.client.table("leads").select("*").eq("phone", phone).execute()

        if not result.data:
            return None
        return self._map_to_lead(result.data[0])

    async def update_state(self, lead_id: UUID, current_state: LeadState) -> Lead | None:
        """Atualiza estado do lead."""
        result = (
            self.client.table("leads")
            .update({"current_state": current_state.value})
            .eq("id", str(lead_id))
            .execute()
        )

        if not result.data:
            return None
        return self._map_to_lead(result.data[0])

    async def update(
        self,
        lead_id: UUID,
        **fields,
    ) -> Lead | None:
        """Atualiza campos do lead."""
        result = self.client.table("leads").update(fields).eq("id", str(lead_id)).execute()

        if not result.data:
            return None
        return self._map_to_lead(result.data[0])

    async def mark_booking_created(self, lead_id: UUID) -> Lead | None:
        """Marca booking criado no lead."""
        return await self.update(
            lead_id,
            has_booking=True,
            current_state=LeadState.POST_BOOKING_PENDING_MATERIALS.value,
        )

    async def mark_materials_sent(self, lead_id: UUID) -> Lead | None:
        """Marca materiais enviados."""
        return await self.update(
            lead_id,
            materials_sent=True,
            current_state=LeadState.POST_BOOKING_PENDING_CHECKLIST.value,
        )

    async def mark_checklist_sent(self, lead_id: UUID) -> Lead | None:
        """Marca checklist enviado."""
        return await self.update(
            lead_id,
            checklist_sent=True,
            current_state=LeadState.SCHEDULED.value,
        )

    async def mark_no_money(self, lead_id: UUID) -> Lead | None:
        """Marca lead como sem dinheiro."""
        return await self.update(
            lead_id,
            no_money_flag=True,
            current_state=LeadState.NO_MONEY.value,
        )

    async def mark_paused_by_human(self, lead_id: UUID) -> Lead | None:
        """Marca lead como pausado por humano."""
        return await self.update(
            lead_id,
            owner_mode=OwnerMode.HUMAN.value,
            current_state=LeadState.PAUSED_BY_HUMAN.value,
        )

    async def update_follow_step(self, lead_id: UUID, step: int) -> Lead | None:
        """Atualiza o passo da cadência de follow-up."""
        return await self.update(lead_id, follow_step=step)

    async def reset_follow_step(self, lead_id: UUID) -> Lead | None:
        """Reseta o passo da cadência (lead respondeu)."""
        return await self.update(lead_id, follow_step=0)

    def _map_to_lead(self, data: dict) -> Lead:
        """Mapeia dados do Supabase para Lead."""
        return Lead(
            id=UUID(data["id"]),
            name=data.get("name"),
            email=data.get("email"),
            phone=data.get("phone"),
            company=data.get("company"),
            current_state=LeadState(data["current_state"]),
            owner_mode=OwnerMode(data["owner_mode"]),
            has_booking=data.get("has_booking", False),
            materials_sent=data.get("materials_sent", False),
            checklist_sent=data.get("checklist_sent", False),
            no_money_flag=data.get("no_money_flag", False),
            follow_step=data.get("follow_step", 0),
            follow_scheduled_at=(
                datetime.fromisoformat(data["follow_scheduled_at"])
                if data.get("follow_scheduled_at")
                else None
            ),
            follow_cancelled_at=(
                datetime.fromisoformat(data["follow_cancelled_at"])
                if data.get("follow_cancelled_at")
                else None
            ),
            source=data.get("source"),
            tags=data.get("tags") or [],
            custom_fields=data.get("custom_fields") or {},
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
