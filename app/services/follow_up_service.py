"""Serviço de follow-up com cadência de 4 etapas.

Cadência:
- Follow 1: 30 min  → "bora continuar falando do seu caso?"
- Follow 2: 4 h     → "{{first_name}}?"
- Follow 3: 20 h    → "algumas pessoas não respondem porque acham que é automático..."
- Follow 4: 23 h    → Case + imagem + "Mas enfim, bora falar do seu caso?"

IMPORTANTE: As mensagens de follow são FIXAS (sem LLM). São enviadas
diretamente via serviço de outbound quando o job for executado.
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from app.repositories.follow_jobs_repository import FollowJobsRepository

logger = logging.getLogger(__name__)


# ============================================
# CADÊNCIA E MENSAGENS DE FOLLOW-UP
# ============================================

FOLLOW_CADENCE = [
    {
        "step": 1,
        "delay_minutes": 30,
        "messages": [
            {"type": "text", "content": "bora continuar falando do seu caso?"},
        ],
    },
    {
        "step": 2,
        "delay_minutes": 240,  # 4 horas
        "messages": [
            {"type": "text", "content": "{{first_name}}?"},
        ],
    },
    {
        "step": 3,
        "delay_minutes": 1200,  # 20 horas
        "messages": [
            {
                "type": "text",
                "content": (
                    "algumas pessoas não respondem porque acham que é automático "
                    "essas mensagens KKK mas enfim tá aí? Kk"
                ),
            },
        ],
    },
    {
        "step": 4,
        "delay_minutes": 1380,  # 23 horas
        "messages": [
            {
                "type": "text",
                "content": (
                    "{{first_name}} olha que legal, lembrei de você na hora! "
                    "Esse cliente fechou mais um contrato de 9.000 quase que automático... "
                    "Ele veio do anúncio, a IA qualificou e, como ele tem poder de "
                    "aquisição, foi levado direto para o fechamento."
                ),
            },
            {
                "type": "image",
                "url": "https://cdn.exemplo.com/imagem-follow.jpeg",
            },
            {
                "type": "text",
                "content": "Mas enfim, bora falar do seu caso?",
            },
        ],
    },
]


def get_follow_messages(step: int, first_name: str = "") -> list[dict]:
    """
    Retorna as mensagens de follow para uma etapa específica.

    Args:
        step: Número do follow (1-4)
        first_name: Nome do lead para substituição de {{first_name}}

    Returns:
        Lista de mensagens formatadas [{type, content/url}]
    """
    if step < 1 or step > len(FOLLOW_CADENCE):
        return []

    follow = FOLLOW_CADENCE[step - 1]
    messages = []

    for msg in follow["messages"]:
        formatted = dict(msg)
        if formatted.get("content"):
            formatted["content"] = formatted["content"].replace(
                "{{first_name}}", first_name or "Ei"
            )
        if formatted.get("type") == "image" and formatted.get("url"):
            try:
                from app.config.settings import get_settings

                s = get_settings()
                if s.follow_up_image_url:
                    formatted["url"] = s.follow_up_image_url
            except Exception:
                pass
        messages.append(formatted)

    return messages


def get_follow_delay(step: int) -> timedelta:
    """
    Retorna o delay para uma etapa de follow.

    Args:
        step: Número do follow (1-4)

    Returns:
        timedelta com o delay
    """
    if step < 1 or step > len(FOLLOW_CADENCE):
        return timedelta(hours=24)  # fallback

    return timedelta(minutes=FOLLOW_CADENCE[step - 1]["delay_minutes"])


def get_next_follow_step(current_step: int) -> int | None:
    """
    Retorna o próximo passo de follow, ou None se já acabou.

    Args:
        current_step: Passo atual (0 = nenhum follow enviado ainda)

    Returns:
        Próximo passo (1-4) ou None
    """
    next_step = current_step + 1
    if next_step > len(FOLLOW_CADENCE):
        return None
    return next_step


class FollowUpService:
    """Serviço para gerenciamento de follow-ups com cadência."""

    def __init__(self):
        self.follow_repo = FollowJobsRepository()

    async def schedule_follow_sequence(
        self,
        lead_id: UUID,
        first_name: str = "",
        current_follow_step: int = 0,
        reason: str | None = None,
    ) -> dict | None:
        """
        Agenda o PRÓXIMO follow-up da cadência para um lead.

        NÃO agenda todos de uma vez — agenda o próximo passo.
        Quando esse passo for executado, o executor agenda o próximo.

        Args:
            lead_id: ID do lead
            first_name: Nome do lead (para personalização)
            current_follow_step: Passo atual (0 = nenhum enviado)
            reason: Motivo do follow-up

        Returns:
            Follow job criado ou None (se cadência acabou)
        """
        next_step = get_next_follow_step(current_follow_step)
        if next_step is None:
            logger.info(f"Cadência de follow-up finalizada para lead {lead_id}")
            return None

        # Cancelar follows pendentes
        await self.cancel_pending_follows(lead_id, reason="Agendando próximo follow")

        # Calcular horário do próximo follow
        delay = get_follow_delay(next_step)
        scheduled_for = datetime.utcnow() + delay

        # Montar mensagens do follow
        messages = get_follow_messages(next_step, first_name)

        # Criar follow job com metadados de cadência
        follow_job = await self.follow_repo.create(
            lead_id=lead_id,
            scheduled_for=scheduled_for,
            reason=reason or f"Follow {next_step}/4",
            metadata={
                "follow_step": next_step,
                "first_name": first_name,
                "messages": messages,
                "delay_minutes": FOLLOW_CADENCE[next_step - 1]["delay_minutes"],
            },
        )

        logger.info(
            f"📩 Follow {next_step}/4 agendado para lead {lead_id}: {scheduled_for} (+{delay})"
        )

        return follow_job

    async def cancel_pending_follows(
        self,
        lead_id: UUID,
        reason: str | None = None,
    ) -> int:
        """
        Cancela todos follow-ups pendentes de um lead.

        Chamado quando:
        - Lead responde (qualquer mensagem)
        - Novo follow é agendado (substitui o anterior)
        - Lead é marcado como NO_MONEY, CLOSED, etc.

        Args:
            lead_id: ID do lead
            reason: Motivo do cancelamento

        Returns:
            Número de follow-ups cancelados
        """
        pending = await self.follow_repo.get_pending_by_lead(lead_id)

        if pending:
            await self.follow_repo.cancel_by_lead(lead_id, reason)
            logger.info(f"Follow-up pendente cancelado para lead {lead_id}")
            return 1

        return 0

    async def get_pending_follow(self, lead_id: UUID) -> dict | None:
        """
        Busca follow-up pendente de um lead.

        Returns:
            Follow job ou None
        """
        return await self.follow_repo.get_pending_by_lead(lead_id)

    async def complete_follow(self, job_id: UUID) -> dict | None:
        """
        Marca follow-up como completado.

        Returns:
            Follow job atualizado ou None
        """
        result = await self.follow_repo.complete(job_id)
        logger.info(f"Follow-up completado: {job_id}")
        return result

    async def get_overdue_follows(self, limit: int = 100) -> list[dict]:
        """
        Busca follow-ups vencidos (para o worker processar).

        Returns:
            Lista de follow jobs vencidos (scheduled_for <= now)
        """
        return await self.follow_repo.get_overdue(limit=limit)


# Singleton
_follow_up_service: FollowUpService | None = None


def get_follow_up_service() -> FollowUpService:
    """Retorna instância singleton do FollowUpService."""
    global _follow_up_service
    if _follow_up_service is None:
        _follow_up_service = FollowUpService()
    return _follow_up_service
