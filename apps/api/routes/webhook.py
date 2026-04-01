"""Rota de webhook do Chatwoot.

Recebe eventos do Chatwoot (message_created, conversation_created, etc.)
e processa mensagens incoming via o pipeline do agente LangGraph.

Configuração no Chatwoot:
  Settings → Integrations → Webhooks → Adicionar
  URL: https://seu-dominio.com/webhook/chatwoot
  Eventos: message_created
"""

import hashlib
import hmac
import logging
import time

from fastapi import APIRouter, Header, HTTPException, Request

from app.agent.graph import run_agent
from app.config.settings import get_settings
from app.integrations.chatwoot.client import get_chatwoot_client
from app.integrations.chatwoot.schemas import ChatwootWebhookPayload
from app.middleware.tenant import resolve_tenant_by_chatwoot_account
from app.state.lead_states import AgentState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["Webhooks"])


def _verify_signature(
    payload_body: bytes,
    signature: str | None,
    secret: str,
) -> bool:
    """Verifica a assinatura HMAC do webhook do Chatwoot."""
    if not secret or not signature:
        return True  # Se não tem secret configurado, aceita tudo

    expected = hmac.new(
        secret.encode(),
        payload_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@router.post("/chatwoot")
async def chatwoot_webhook(
    request: Request,
    x_chatwoot_signature: str | None = Header(None, alias="x-chatwoot-signature"),
):
    """Endpoint de webhook do Chatwoot.

    Processa eventos `message_created` com `message_type = incoming`.
    Ignora mensagens outgoing, privadas e outros eventos.

    Fluxo:
    1. Valida assinatura HMAC (se configurada)
    2. Parse do payload
    3. Filtra apenas mensagens incoming
    4. Monta session_id único baseado no Chatwoot conversation ID
    5. Roda o agente LangGraph
    6. Envia resposta de volta ao Chatwoot

    Returns:
        {"status": "ok"} para todos os eventos (Chatwoot espera 200)
    """
    settings = get_settings()
    start_time = time.time()

    # ── 1. Ler body e verificar assinatura ──────────────────

    raw_body = await request.body()

    if settings.chatwoot_webhook_secret:
        if not _verify_signature(
            raw_body,
            x_chatwoot_signature,
            settings.chatwoot_webhook_secret,
        ):
            logger.warning("Webhook Chatwoot: assinatura inválida")
            raise HTTPException(status_code=401, detail="Invalid signature")

    # ── 2. Parse do payload ─────────────────────────────────

    try:
        payload = ChatwootWebhookPayload.model_validate_json(raw_body)
    except Exception as e:
        logger.error(f"Webhook Chatwoot: erro no parse: {e}")
        return {"status": "ignored", "reason": "invalid_payload"}

    # ── 3. Filtrar — só processar mensagens incoming ────────

    if not payload.is_incoming_message:
        logger.debug(
            f"Webhook Chatwoot ignorado: event={payload.event}, "
            f"type={payload.message_type}, private={payload.private}"
        )
        return {"status": "ignored", "reason": "not_incoming_message"}

    if not payload.content and not payload.has_media:
        logger.debug("Webhook Chatwoot ignorado: sem conteúdo e sem mídia")
        return {"status": "ignored", "reason": "empty_message"}

    chatwoot_conv_id = payload.chatwoot_conversation_id
    if not chatwoot_conv_id:
        logger.warning("Webhook Chatwoot: sem conversation ID")
        return {"status": "ignored", "reason": "no_conversation_id"}

    # ── 4. Resolver tenant (multi-tenancy) ──────────────────

    tenant = None
    tenant_id = None
    if payload.conversation and payload.conversation.account_id:
        tenant = await resolve_tenant_by_chatwoot_account(payload.conversation.account_id)
        if tenant:
            tenant_id = tenant.tenant_id
            logger.info(f"Tenant resolvido: {tenant.slug} ({tenant.tenant_id})")

    # ── 5. Montar estado do agente ──────────────────────────

    # session_id único baseado no Chatwoot para manter continuidade
    session_id = f"chatwoot_{chatwoot_conv_id}"

    # Determinar tipo de mensagem
    message_type = "text"
    media_url = None
    media_type_str = None

    if payload.has_media:
        media_url = payload.first_attachment_url
        att_type = payload.first_attachment_type
        if att_type in ("audio",):
            message_type = "audio"
            media_type_str = "audio"
        elif att_type in ("image",):
            message_type = "image"
            media_type_str = "image"

    incoming_text = payload.content or ""

    logger.info(
        f"Webhook Chatwoot: conv={chatwoot_conv_id}, "
        f"contact={payload.contact_name}, "
        f"msg_type={message_type}, "
        f"text_len={len(incoming_text)}"
    )

    agent_state = AgentState(
        session_id=session_id,
        tenant_id=tenant_id,
        incoming_message=incoming_text,
        incoming_message_type=message_type,
        media_url=media_url,
        media_type=media_type_str,
        metadata={
            "lead_name": payload.contact_name,
            "lead_email": payload.contact_email,
            "lead_phone": payload.contact_phone,
            "channel": "chatwoot",
            "chatwoot_conversation_id": chatwoot_conv_id,
            "chatwoot_message_id": payload.id,
            "chatwoot_sender_id": payload.sender.id if payload.sender else None,
        },
    )

    # ── 5. Executar agente ──────────────────────────────────

    try:
        result = await run_agent(agent_state)
    except Exception as e:
        logger.error(f"Webhook Chatwoot: erro no agente: {e}", exc_info=True)
        # Enviar nota privada com o erro
        try:
            chatwoot = get_chatwoot_client()
            await chatwoot.send_activity(
                conversation_id=chatwoot_conv_id,
                content=f"⚠️ Erro no SDR Agent: {str(e)[:200]}",
            )
        except Exception:
            pass
        return {"status": "error", "reason": str(e)[:200]}

    # ── 6. Enviar resposta de volta ao Chatwoot ─────────────

    reply = result.reply_text
    if not reply:
        logger.info("Webhook Chatwoot: sem resposta (paused/empty)")
        return {"status": "ok", "reason": "no_reply"}

    try:
        chatwoot = get_chatwoot_client()

        # Separar blocos de texto por \\ (separador de mensagens)
        blocks = [b.strip() for b in reply.split("\\\\") if b.strip()]
        if not blocks:
            blocks = [reply]

        for block in blocks:
            # Substituir tags [MEDIA:XXX] por URLs reais se configurado
            await chatwoot.send_message(
                conversation_id=chatwoot_conv_id,
                content=block,
            )

        # Atualizar custom_attributes do contato com estágio
        if payload.sender and payload.sender.id:
            new_state = result.next_state.value if result.next_state else result.current_state.value
            try:
                await chatwoot.update_contact(
                    contact_id=payload.sender.id,
                    custom_attributes={
                        "sdr_stage": new_state,
                        "sdr_last_interaction": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    },
                )
            except Exception as e:
                logger.warning(f"Erro ao atualizar contato Chatwoot: {e}")

        elapsed = time.time() - start_time
        logger.info(
            f"Webhook Chatwoot processado: conv={chatwoot_conv_id}, "
            f"blocks={len(blocks)}, elapsed={elapsed:.1f}s"
        )

    except Exception as e:
        logger.error(f"Erro ao enviar resposta ao Chatwoot: {e}", exc_info=True)
        return {"status": "error", "reason": f"send_failed: {str(e)[:100]}"}

    return {
        "status": "ok",
        "conversation_id": chatwoot_conv_id,
        "blocks_sent": len(blocks),
        "state": result.next_state.value if result.next_state else result.current_state.value,
        "elapsed_s": round(time.time() - start_time, 2),
    }


@router.get("/chatwoot/health")
async def chatwoot_webhook_health():
    """Health check do webhook do Chatwoot."""
    settings = get_settings()
    return {
        "status": "ok",
        "chatwoot_enabled": settings.chatwoot_enabled,
        "chatwoot_base_url": settings.chatwoot_base_url if settings.chatwoot_enabled else None,
    }
