"""Serviço de booking - gerencia agendamentos."""

import logging
from datetime import datetime
from uuid import UUID

from app.domain.booking import Booking
from app.integrations.calcom.client import get_calcom_client
from app.repositories.bookings_repository import BookingsRepository
from app.repositories.leads_repository import LeadsRepository

logger = logging.getLogger(__name__)


class BookingService:
    """Serviço para gerenciamento de bookings."""

    def __init__(self):
        self.bookings_repo = BookingsRepository()
        self.leads_repo = LeadsRepository()
        self.calcom_client = get_calcom_client()

    async def list_available_slots(
        self,
        start_date: str,
        end_date: str,
        event_type_id: int | None = None,
    ) -> list[dict]:
        """
        Lista slots disponíveis para agendamento.

        Args:
            start_date: Data inicial (ISO 8601)
            end_date: Data final (ISO 8601)
            event_type_id: ID do tipo de evento

        Returns:
            Lista de slots disponíveis
        """
        if not self.calcom_client.is_available():
            logger.warning("Cal.com não configurado, retornando slots vazios")
            return []

        try:
            slots = await self.calcom_client.list_slots(
                start_date=start_date,
                end_date=end_date,
                event_type_id=event_type_id,
            )

            return [slot.model_dump() for slot in slots]

        except Exception as e:
            logger.error(f"Erro ao buscar slots: {e}")
            return []

    async def create_booking(
        self,
        lead_id: UUID,
        start_time: datetime,
        end_time: datetime,
        name: str,
        email: str,
        timezone: str = "America/Sao_Paulo",
        title: str | None = None,
        description: str | None = None,
    ) -> Booking | None:
        """
        Cria um booking (local + Cal.com).

        Args:
            lead_id: ID do lead
            start_time: Data/hora inicial
            end_time: Data/hora final
            name: Nome do lead
            email: Email do lead
            timezone: Timezone
            title: Título do booking
            description: Descrição

        Returns:
            Booking criado ou None
        """
        calcom_booking = None

        # Criar no Cal.com se disponível
        if self.calcom_client.is_available():
            try:
                calcom_booking = await self._create_calcom_booking(
                    name=name,
                    email=email,
                    start=start_time.isoformat(),
                    timezone=timezone,
                )
                logger.info(f"Booking criado no Cal.com: {calcom_booking.id}")
            except Exception as e:
                logger.error(f"Erro ao criar booking no Cal.com: {e}")

        # Criar no banco local
        booking = await self.bookings_repo.create(
            lead_id=lead_id,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone,
            title=title,
            description=description,
            calcom_booking_id=calcom_booking.id if calcom_booking else None,
            calcom_booking_uid=calcom_booking.uid if calcom_booking else None,
            meeting_url=calcom_booking.effective_meeting_url if calcom_booking else None,
            calcom_data=calcom_booking.model_dump() if calcom_booking else {},
        )

        # Atualizar lead
        await self.leads_repo.mark_booking_created(lead_id)

        logger.info(f"Booking criado localmente: {booking.id}")
        return booking

    async def _create_calcom_booking(
        self,
        name: str,
        email: str,
        start: str,
        timezone: str,
    ) -> dict | None:
        """Cria booking no Cal.com."""
        if not self.calcom_client.is_available():
            return None

        return await self.calcom_client.create_booking(
            event_type_id=self.calcom_client.event_type_id,
            start=start,
            name=name,
            email=email,
            timezone=timezone,
        )

    async def get_booking(self, booking_id: UUID) -> Booking | None:
        """Busca booking por ID."""
        return await self.bookings_repo.get_by_id(booking_id)

    async def get_active_booking(self, lead_id: UUID) -> Booking | None:
        """Busca booking ativo de um lead."""
        return await self.bookings_repo.get_active_by_lead(lead_id)

    async def cancel_booking(
        self,
        booking_id: UUID,
        reason: str | None = None,
    ) -> bool:
        """
        Cancela booking (local + Cal.com).

        Args:
            booking_id: ID do booking
            reason: Motivo do cancelamento

        Returns:
            True se cancelado com sucesso
        """
        booking = await self.bookings_repo.get_by_id(booking_id)
        if not booking:
            return False

        # Cancelar no Cal.com se existir
        calcom_uid = getattr(booking, "calcom_booking_uid", None) or str(
            booking.calcom_booking_id or ""
        )
        if calcom_uid and self.calcom_client.is_available():
            try:
                await self.calcom_client.cancel_booking(
                    booking_uid=calcom_uid,
                    reason=reason,
                )
                logger.info(f"Booking cancelado no Cal.com: {booking.calcom_booking_id}")
            except Exception as e:
                logger.error(f"Erro ao cancelar no Cal.com: {e}")

        # Cancelar local
        await self.bookings_repo.cancel(booking_id, reason)
        logger.info(f"Booking cancelado localmente: {booking_id}")

        return True

    async def reschedule_booking(
        self,
        booking_id: UUID,
        new_start: datetime,
        new_end: datetime,
        reason: str | None = None,
    ) -> Booking | None:
        """
        Remarca booking.

        Args:
            booking_id: ID do booking original
            new_start: Nova data/hora inicial
            new_end: Nova data/hora final
            reason: Motivo da remarcação

        Returns:
            Novo booking ou None
        """
        booking = await self.bookings_repo.get_by_id(booking_id)
        if not booking:
            return None

        # Remarcar no Cal.com se existir
        new_calcom_booking = None
        calcom_uid = getattr(booking, "calcom_booking_uid", None) or str(
            booking.calcom_booking_id or ""
        )
        if calcom_uid and self.calcom_client.is_available():
            try:
                new_calcom_booking = await self.calcom_client.reschedule_booking(
                    booking_uid=calcom_uid,
                    new_start=new_start.isoformat(),
                    reason=reason,
                )
                logger.info(f"Booking remarcado no Cal.com: {new_calcom_booking.id}")
            except Exception as e:
                logger.error(f"Erro ao remarcar no Cal.com: {e}")

        # Criar novo booking local
        new_booking = await self.bookings_repo.create(
            lead_id=booking.lead_id,
            start_time=new_start,
            end_time=new_end,
            timezone=booking.timezone,
            title=booking.title,
            description=booking.description,
            calcom_booking_id=new_calcom_booking.id if new_calcom_booking else None,
            calcom_booking_uid=new_calcom_booking.uid if new_calcom_booking else None,
            meeting_url=new_calcom_booking.effective_meeting_url
            if new_calcom_booking
            else booking.meeting_url,
            calcom_data=new_calcom_booking.model_dump()
            if new_calcom_booking
            else booking.calcom_data,
            rescheduled_from_id=booking_id,
        )

        # Cancelar booking antigo
        await self.bookings_repo.cancel(booking_id, reason or "Remarcado")

        logger.info(f"Booking remarcado localmente: {new_booking.id}")
        return new_booking


# Singleton
_booking_service: BookingService | None = None


def get_booking_service() -> BookingService:
    """Retorna instância singleton do BookingService."""
    global _booking_service
    if _booking_service is None:
        _booking_service = BookingService()
    return _booking_service
