"""Cliente Cal.com API v2.

Autenticação via Bearer token + header cal-api-version,
idêntico ao workflow n8n original que funcionava.
Testado e confirmado com chave cal_live_*.
"""

import logging
from typing import Any

import httpx
from pydantic import BaseModel

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Versões da API v2 (conforme workflow n8n original)
CALCOM_API_VERSION_DEFAULT = "2024-08-13"
CALCOM_API_VERSION_SLOTS = "2024-09-04"


class CalcomSlot(BaseModel):
    """Slot de agendamento do Cal.com v2 (formato range)."""

    start: str  # ISO 8601 com timezone (ex: 2026-04-01T09:00:00.000-03:00)
    end: str    # ISO 8601 com timezone


class CalcomBooking(BaseModel):
    """Booking do Cal.com v2."""

    id: int | None = None
    uid: str | None = None
    title: str | None = None
    description: str | None = None
    start: str | None = None
    end: str | None = None
    startTime: str | None = None
    endTime: str | None = None
    status: str | None = None
    duration: int | None = None
    meetingUrl: str | None = None
    meeting_url: str | None = None
    attendees: list[dict] | None = None
    hosts: list[dict] | None = None
    eventTypeId: int | None = None

    @property
    def effective_start(self) -> str | None:
        return self.start or self.startTime

    @property
    def effective_end(self) -> str | None:
        return self.end or self.endTime

    @property
    def effective_meeting_url(self) -> str | None:
        return self.meetingUrl or self.meeting_url


class CalcomClient:
    """Cliente para API v2 do Cal.com.

    Autenticação via Bearer token + header cal-api-version,
    replicando exatamente o workflow n8n funcional.
    """

    def __init__(self):
        self.base_url = settings.calcom_base_url.rstrip("/")
        self.api_key = settings.calcom_api_key
        self.event_type_id = settings.calcom_event_type_id

    def _headers(self, api_version: str = CALCOM_API_VERSION_DEFAULT) -> dict:
        """Headers para API v2 (idêntico ao n8n)."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "cal-api-version": api_version,
        }

    def is_available(self) -> bool:
        """Verifica se Cal.com está configurado."""
        return bool(self.api_key and self.event_type_id)

    async def list_slots(
        self,
        start_date: str,
        end_date: str,
        event_type_id: int | None = None,
        timezone: str = "America/Sao_Paulo",
    ) -> list[CalcomSlot]:
        """
        Lista slots disponíveis (API v2 /slots com format=range).

        Réplica exata do nó 'disponibilidade_agenda' do n8n.
        Usa cal-api-version: 2024-09-04 para slots.

        A resposta v2 com format=range retorna:
        { data: { "YYYY-MM-DD": [{start, end}, ...] } }

        Args:
            start_date: Data inicial (ISO 8601 UTC, ex: 2026-04-01T00:00:00Z)
            end_date: Data final (ISO 8601 UTC, ex: 2026-04-02T23:59:59Z)
            event_type_id: ID do tipo de evento (usa default se None)
            timezone: Timezone para os slots

        Returns:
            Lista de slots disponíveis
        """
        if not self.is_available():
            return []

        event_id = event_type_id or self.event_type_id

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/slots",
                headers=self._headers(CALCOM_API_VERSION_SLOTS),
                params={
                    "eventTypeId": event_id,
                    "start": start_date,
                    "end": end_date,
                    "timeZone": timezone,
                    "format": "range",
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # API v2 format=range retorna:
            # { status: "success", data: { "2026-04-01": [{start, end}, ...] } }
            slot_data = data.get("data", {})

            slots = []
            if isinstance(slot_data, dict):
                for _date, day_slots in slot_data.items():
                    if isinstance(day_slots, list):
                        for slot in day_slots:
                            slots.append(CalcomSlot(
                                start=slot.get("start", ""),
                                end=slot.get("end", ""),
                            ))

            logger.info(f"Cal.com v2: {len(slots)} slots encontrados")
            return slots

    async def create_booking(
        self,
        event_type_id: int,
        start: str,
        name: str,
        email: str,
        timezone: str = "America/Sao_Paulo",
        metadata: dict | None = None,
        booking_title: str | None = None,
    ) -> CalcomBooking:
        """
        Cria um novo booking (API v2).

        Réplica exata do nó 'agendar_reuniao' do n8n.
        Formato v2: attendee é objeto nested, não campos flat.

        Args:
            event_type_id: ID do tipo de evento
            start: Data/hora inicial (ISO 8601 UTC com Z)
            name: Nome do lead
            email: Email do lead
            timezone: Timezone do attendee
            metadata: Metadados adicionais
            booking_title: Título customizado

        Returns:
            Booking criado
        """
        if not self.is_available():
            raise ValueError("Cal.com não está configurado")

        # Formato v2 idêntico ao n8n: attendee como objeto separado
        booking_data: dict[str, Any] = {
            "eventTypeId": event_type_id,
            "start": start,
            "attendee": {
                "name": name,
                "email": email,
                "timeZone": timezone,
            },
        }

        # Título customizado via bookingFieldsResponses (como no n8n)
        if booking_title:
            booking_data["bookingFieldsResponses"] = {
                "title": booking_title,
            }

        if metadata:
            booking_data["metadata"] = metadata

        logger.info(f"Cal.com v2: Criando booking para {email} em {start}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bookings",
                headers=self._headers(),
                json=booking_data,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # API v2 retorna { status: "success", data: { ... } }
            booking_raw = data.get("data", data)

            # Filtrar para campos válidos do modelo
            valid_fields = set(CalcomBooking.model_fields.keys())
            filtered = {k: v for k, v in booking_raw.items() if k in valid_fields}

            logger.info(
                f"Cal.com v2: Booking criado - "
                f"id: {filtered.get('id')}, uid: {filtered.get('uid')}"
            )
            return CalcomBooking(**filtered)

    async def get_booking(self, booking_uid: str) -> CalcomBooking:
        """
        Busca um booking por UID (API v2).

        Réplica do nó 'buscar_reunião_especifica' do n8n.

        Args:
            booking_uid: UID do booking (string)

        Returns:
            Booking encontrado
        """
        if not self.is_available():
            raise ValueError("Cal.com não está configurado")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/bookings/{booking_uid}",
                headers=self._headers(),
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            booking_raw = data.get("data", data)
            valid_fields = set(CalcomBooking.model_fields.keys())
            filtered = {k: v for k, v in booking_raw.items() if k in valid_fields}
            return CalcomBooking(**filtered)

    async def list_bookings(
        self,
        attendee_email: str | None = None,
        take: int = 100,
    ) -> list[CalcomBooking]:
        """
        Lista bookings existentes (API v2).

        Réplica dos nós 'buscar_bookings' e 'buscar_booking_por_email' do n8n.

        Args:
            attendee_email: Filtrar por email do attendee
            take: Número máximo de resultados

        Returns:
            Lista de bookings
        """
        if not self.is_available():
            return []

        params: dict[str, Any] = {"take": take}
        if attendee_email:
            params["attendeeEmail"] = attendee_email

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/bookings",
                headers=self._headers(),
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # API v2: { status: "success", data: [...] }
            raw_bookings = data.get("data", [])
            if isinstance(raw_bookings, list):
                valid_fields = set(CalcomBooking.model_fields.keys())
                return [
                    CalcomBooking(**{k: v for k, v in b.items() if k in valid_fields})
                    for b in raw_bookings
                ]
            return []

    async def cancel_booking(
        self, booking_uid: str, reason: str | None = None
    ) -> bool:
        """
        Cancela um booking (API v2 - POST .../cancel).

        Réplica exata do nó 'cancela_reuniao' do n8n.

        Args:
            booking_uid: UID do booking (string)
            reason: Motivo do cancelamento

        Returns:
            True se cancelado com sucesso
        """
        if not self.is_available():
            raise ValueError("Cal.com não está configurado")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bookings/{booking_uid}/cancel",
                headers=self._headers(),
                json={"cancellationReason": reason or "Solicitação do cliente"},
                timeout=30.0,
            )
            response.raise_for_status()
            logger.info(f"Cal.com v2: Booking {booking_uid} cancelado")
            return True

    async def reschedule_booking(
        self,
        booking_uid: str,
        new_start: str,
        reason: str | None = None,
    ) -> CalcomBooking:
        """
        Remarca um booking (API v2 - POST .../reschedule).

        Réplica exata do nó 'reagenda_reuniao' do n8n.

        Args:
            booking_uid: UID do booking original
            new_start: Nova data/hora (ISO 8601 UTC com Z)
            reason: Motivo da remarcação

        Returns:
            Novo booking
        """
        if not self.is_available():
            raise ValueError("Cal.com não está configurado")

        body: dict[str, Any] = {"start": new_start}
        if reason:
            body["reschedulingReason"] = reason

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bookings/{booking_uid}/reschedule",
                headers=self._headers(),
                json=body,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            booking_raw = data.get("data", data)
            valid_fields = set(CalcomBooking.model_fields.keys())
            filtered = {k: v for k, v in booking_raw.items() if k in valid_fields}
            logger.info(f"Cal.com v2: Booking remarcado - uid: {filtered.get('uid')}")
            return CalcomBooking(**filtered)


# Singleton global
_calcom_instance: CalcomClient | None = None


def get_calcom_client() -> CalcomClient:
    """Retorna instância singleton do cliente Cal.com."""
    global _calcom_instance
    if _calcom_instance is None:
        _calcom_instance = CalcomClient()
    return _calcom_instance
