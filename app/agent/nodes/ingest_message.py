"""Node: ingest_message - Processa mensagem recebida."""

import logging

from app.state.lead_states import AgentState

logger = logging.getLogger(__name__)


async def ingest_message(state: AgentState) -> AgentState:
    """
    Node de ingestão de mensagem.

    Responsabilidades:
    - Validar mensagem recebida
    - Normalizar tipo de mensagem
    - Preparar contexto inicial
    """
    logger.debug("Iniciando ingestão de mensagem")

    # Validar se há mensagem ou mídia
    if not state.incoming_message and not state.media_url:
        state.error = "Nenhuma mensagem ou mídia recebida"
        logger.warning("Mensagem vazia recebida")
        return state

    # Normalizar tipo de mensagem
    if state.media_url:
        # Mensagem com mídia
        if state.media_type in ("audio", "image"):
            state.incoming_message_type = state.media_type
            logger.debug(f"Mensagem de mídia: {state.media_type}")
        else:
            state.incoming_message_type = "text"
    else:
        # Mensagem de texto pura
        state.incoming_message_type = "text"

    # Combinar mensagem com transcrição/análise se existir
    if state.media_transcription and state.incoming_message_type == "audio":
        # Para áudio, usar transcrição como conteúdo principal
        if state.incoming_message:
            state.incoming_message = f"{state.incoming_message}\n\n[Transcrição do áudio: {state.media_transcription}]"
        else:
            state.incoming_message = state.media_transcription
        logger.debug("Usando transcrição de áudio como conteúdo")

    if state.media_analysis and state.incoming_message_type == "image":
        # Para imagem, adicionar análise como contexto
        if state.incoming_message:
            state.incoming_message = f"{state.incoming_message}\n\n[Análise da imagem: {state.media_analysis}]"
        else:
            state.incoming_message = f"[Imagem enviada: {state.media_analysis}]"
        logger.debug("Usando análise de imagem como contexto")

    # Registrar no metadata
    state.metadata["message_ingested"] = True
    state.metadata["message_type"] = state.incoming_message_type
    state.metadata["has_media"] = bool(state.media_url)

    logger.debug("Ingestão de mensagem concluída")
    return state
