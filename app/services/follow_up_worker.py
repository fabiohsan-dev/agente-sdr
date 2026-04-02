"""Worker de follow-up — processa jobs vencidos.

Este worker deve ser executado como cron/scheduler (a cada 1-2 minutos).
Ele busca follow_jobs com status='pending' e scheduled_for <= NOW(),
envia as mensagens e agenda o próximo step da cadência.

Execução:
    python -m app.services.follow_up_worker

    Ou via cron:
    */1 * * * * cd /path/to/project && python -m app.services.follow_up_worker
"""

import asyncio
import logging
from uuid import UUID

from app.repositories.follow_jobs_repository import FollowJobsRepository
from app.repositories.leads_repository import LeadsRepository
from app.services.follow_up_service import (
    FollowUpService,
    get_follow_messages,
    get_next_follow_step,
)

logger = logging.getLogger(__name__)


class FollowUpWorker:
    """Processa follow jobs vencidos e envia mensagens."""

    def __init__(self):
        self.follow_repo = FollowJobsRepository()
        self.leads_repo = LeadsRepository()
        self.follow_service = FollowUpService()

    async def process_overdue_follows(self) -> dict:
        """
        Busca e processa todos os follow jobs vencidos.

        Para cada job:
        1. Valida que o lead ainda está em estado ativo
        2. Envia as mensagens do follow (via outbound)
        3. Marca o job como completed
        4. Agenda o próximo step da cadência
        5. Atualiza follow_step no lead

        Returns:
            Resumo: {processed, succeeded, failed, skipped}
        """
        stats = {"processed": 0, "succeeded": 0, "failed": 0, "skipped": 0}

        # 1. Buscar jobs vencidos
        overdue_jobs = await self.follow_service.get_overdue_follows(limit=50)

        if not overdue_jobs:
            logger.debug("Nenhum follow-up vencido para processar")
            return stats

        logger.info(f"📩 Processando {len(overdue_jobs)} follow(s) vencido(s)")

        for job in overdue_jobs:
            stats["processed"] += 1
            job_id = UUID(job["id"])
            lead_id = UUID(job["lead_id"])
            job_metadata = job.get("metadata", {})
            current_step = job_metadata.get("follow_step", 1)
            first_name = job_metadata.get("first_name", "")

            try:
                # 2. Validar que lead ainda está ativo (não pausado/fechado)
                lead = await self.leads_repo.get_by_id(lead_id)
                if not lead:
                    logger.warning(f"Lead {lead_id} não encontrado, cancelando job {job_id}")
                    await self.follow_repo.cancel(job_id, reason="Lead não encontrado")
                    stats["skipped"] += 1
                    continue

                # Estados que impedem envio de follow
                blocked_states = {
                    "PAUSED_BY_HUMAN",
                    "NO_MONEY",
                    "CLOSED",
                    "SCHEDULED",
                    "POST_BOOKING_PENDING_MATERIALS",
                    "POST_BOOKING_PENDING_CHECKLIST",
                }
                if lead.current_state.value in blocked_states:
                    logger.info(
                        f"Lead {lead_id} em estado {lead.current_state.value} — "
                        f"cancelando follow {job_id}"
                    )
                    await self.follow_repo.cancel(
                        job_id,
                        reason=f"Lead em estado bloqueante: {lead.current_state.value}",
                    )
                    stats["skipped"] += 1
                    continue

                # 3. Obter mensagens do follow
                messages = job_metadata.get("messages") or get_follow_messages(
                    current_step, first_name
                )

                # 4. Enviar mensagens via outbound
                await self._send_follow_messages(lead_id, messages)
                logger.info(
                    f"✅ Follow {current_step}/4 enviado para lead {lead_id} "
                    f"({len(messages)} mensagem(s))"
                )

                # 5. Marcar job como completed
                await self.follow_repo.complete(job_id)

                # 6. Agendar próximo step (se ainda há passos)
                next_step = get_next_follow_step(current_step)
                if next_step is not None:
                    await self.follow_service.schedule_follow_sequence(
                        lead_id=lead_id,
                        first_name=first_name,
                        current_follow_step=current_step,
                        reason=f"Continuação automática da cadência (step {next_step}/4)",
                    )
                    # Atualizar follow_step no lead
                    await self.leads_repo.update_follow_step(lead_id, next_step)
                    logger.info(f"📩 Próximo follow ({next_step}/4) agendado para lead {lead_id}")
                else:
                    logger.info(f"🏁 Cadência finalizada para lead {lead_id} (4/4 completos)")
                    # Reset follow_step para indicar cadência completa
                    await self.leads_repo.reset_follow_step(lead_id)

                stats["succeeded"] += 1

            except Exception as e:
                logger.error(f"❌ Erro ao processar follow job {job_id}: {type(e).__name__}: {e}")
                await self.follow_repo.mark_failed(job_id, error=str(e))
                stats["failed"] += 1

        logger.info(
            f"📊 Follow worker finalizado: "
            f"{stats['processed']} processados, "
            f"{stats['succeeded']} enviados, "
            f"{stats['failed']} falharam, "
            f"{stats['skipped']} ignorados"
        )

        return stats

    async def _send_follow_messages(self, lead_id: UUID, messages: list[dict]) -> None:
        """
        Envia as mensagens de follow para o lead.

        Integra com o serviço de outbound real.
        Cada mensagem pode ser: text, image, audio.
        """
        try:
            from app.services.outbound_service import get_outbound_service

            outbound = get_outbound_service()

            for msg in messages:
                msg_type = msg.get("type", "text")

                if msg_type == "text":
                    await outbound.send_text(
                        lead_id=lead_id,
                        text=msg["content"],
                    )
                elif msg_type == "image":
                    await outbound.send_image(
                        lead_id=lead_id,
                        image_url=msg["url"],
                        caption=msg.get("caption"),
                    )
                else:
                    logger.warning(f"Tipo de mensagem não suportado: {msg_type}")

        except Exception as e:
            logger.error(f"Erro ao enviar follow message para lead {lead_id}: {e}")
            raise


async def run_worker():
    """Executa o worker uma vez (para uso com cron externo)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    worker = FollowUpWorker()
    stats = await worker.process_overdue_follows()
    return stats


if __name__ == "__main__":
    asyncio.run(run_worker())
