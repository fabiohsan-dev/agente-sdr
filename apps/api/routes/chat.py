"""Rota de chat."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.agent.graph import run_agent
from app.middleware.tenant import TenantContext, get_tenant_optional
from app.repositories.leads_repository import LeadsRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.state.lead_states import AgentState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    tenant: TenantContext | None = Depends(get_tenant_optional),
) -> ChatResponse:
    """
    Endpoint principal de chat.

    Processa mensagem recebida, executa agente LangGraph e retorna resposta.

    Args:
        request: Request de chat com mensagem e session_id

    Returns:
        Resposta do agente
    """
    logger.info(f"Recebida mensagem de session_id={request.session_id}")

    # ============================================
    # VALIDAR REQUEST
    # ============================================

    if not request.message and not request.media_url:
        raise HTTPException(status_code=400, detail="Mensagem ou media_url é obrigatório")

    # ============================================
    # BUSCAR/CREAR LEAD
    # ============================================

    leads_repo = LeadsRepository()
    lead = None

    # NÃO passar lead_id no agent_state!
    # O load_state deve buscar pela session_id primeiro
    lead_id = None

    if request.lead_email:
        lead = await leads_repo.get_by_email(request.lead_email)
        if lead:
            lead_id = lead.id
            logger.debug(f"Lead encontrado por email: {lead.id}")

    if not lead and request.lead_name:
        # Criar novo lead apenas se não encontrou por email
        lead = await leads_repo.create(
            email=request.lead_email,
            name=request.lead_name,
            source="playground",
        )
        lead_id = lead.id
        logger.info(f"Novo lead criado: {lead.id}")

    # ============================================
    # SALVAR MENSAGEM INBOUND
    # ============================================

    # Nota: conversation_id será criado pelo LangGraph no node load_state
    # Aqui apenas salvamos a mensagem se já existir conversation

    # ============================================
    # PREPARAR ESTADO DO AGENTE
    # ============================================

    # IMPORTANTE: NÃO passar lead_id se temos session_id!
    # O load_state deve buscar conversation pela session_id PRIMEIRO
    # Se passar lead_id, ele pula a busca e cria novo lead

    agent_state = AgentState(
        lead_id=None,  # ← NÃO passar lead_id! Load_state busca por session_id
        session_id=request.session_id,
        tenant_id=tenant.tenant_id if tenant else None,
        incoming_message=request.message,
        incoming_message_type=request.message_type,
        media_url=request.media_url,
        media_type=request.metadata.get("media_type"),
        media_transcription=request.metadata.get("transcription"),
        media_analysis=request.metadata.get("analysis"),
        metadata={
            "lead_email": request.lead_email,
            "lead_name": request.lead_name,
            "channel": "playground",
            "tenant_slug": tenant.slug if tenant else None,
            **request.metadata,
        },
    )

    # ============================================
    # EXECUTAR AGENTE
    # ============================================

    try:
        result = await run_agent(agent_state)
    except Exception as e:
        logger.error(f"Erro na execução do agente: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no agente: {str(e)}")

    # ============================================
    # VALIDAR RESPOSTA
    # ============================================

    if not result.reply_text:
        # Se não há resposta (ex: PAUSED_BY_HUMAN), retornar vazio
        return ChatResponse(
            reply="",
            state=result.current_state.value,
            actions=[],
            lead_id=lead_id,
            conversation_id=result.conversation_id,
        )

    # ============================================
    # RETORNAR RESPOSTA
    # ============================================

    return ChatResponse(
        reply=result.reply_text,
        state=result.next_state.value if result.next_state else result.current_state.value,
        actions=result.actions,
        lead_id=lead_id,
        conversation_id=result.conversation_id,
        metadata={
            "latency_ms": result.latency_ms,
            "model_used": result.model_used,
            "state_before": result.state_before.value if result.state_before else None,
            "media": result.metadata.get("media", []),  # ✅ Retornar mídia separada
        },
    )


@router.post("/text")
async def chat_text(
    session_id: str,
    message: str,
    lead_email: str | None = None,
    lead_name: str | None = None,
):
    """
    Endpoint simplificado para chat de texto.

    Args:
        session_id: ID da sessão
        message: Mensagem de texto
        lead_email: Email do lead (opcional)
        lead_name: Nome do lead (opcional)

    Returns:
        Resposta do agente
    """
    request = ChatRequest(
        session_id=session_id,
        message=message,
        message_type="text",
        lead_email=lead_email,
        lead_name=lead_name,
    )
    return await chat(request)


@router.post("/media")
async def chat_media(
    session_id: str,
    media_url: str,
    media_type: str,
    transcription: str | None = None,
    analysis: str | None = None,
    lead_email: str | None = None,
    lead_name: str | None = None,
):
    """
    Endpoint para chat com mídia.

    Args:
        session_id: ID da sessão
        media_url: URL da mídia (CDN)
        media_type: Tipo de mídia (audio, image)
        transcription: Transcrição (para áudio)
        analysis: Análise (para imagem)
        lead_email: Email do lead (opcional)
        lead_name: Nome do lead (opcional)

    Returns:
        Resposta do agente
    """
    request = ChatRequest(
        session_id=session_id,
        message=None,
        message_type=media_type,
        media_url=media_url,
        lead_email=lead_email,
        lead_name=lead_name,
        metadata={
            "media_type": media_type,
            "transcription": transcription,
            "analysis": analysis,
        },
    )
    return await chat(request)
