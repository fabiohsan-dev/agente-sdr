"""Node: maybe_process_media - Processa mídia se necessário."""

import logging

from app.state.guards import BusinessRules
from app.state.lead_states import AgentState

logger = logging.getLogger(__name__)


async def maybe_process_media(state: AgentState) -> AgentState:
    """
    Node de processamento de mídia.

    Responsabilidades:
    - Verificar se há mídia para processar
    - Processar áudio (transcrição)
    - Processar imagem (análise)
    - Atualizar estado com resultados

    NOTA: O processamento real (chamar APIs de transcrição/visão)
    deve ser feito nos serviços. Este node apenas orquestra.
    """
    logger.debug("Verificando processamento de mídia")

    # Verificar se há mídia
    if not state.media_url:
        state.metadata["media_processing"] = "no_media"
        return state

    # Verificar se deve processar
    should_process = BusinessRules.should_process_audio(
        state
    ) or BusinessRules.should_process_image(state)

    if not should_process:
        state.metadata["media_processing"] = "not_required"
        return state

    # ============================================
    # PROCESSAR ÁUDIO
    # ============================================

    if state.media_type == "audio" and not state.media_transcription:
        logger.info("Processando áudio: %s", state.media_url)
        state = await _process_audio(state)

    # ============================================
    # PROCESSAR IMAGEM
    # ============================================

    elif state.media_type == "image" and not state.media_analysis:
        logger.info("Processando imagem: %s", state.media_url)
        state = await _process_image(state)

    state.metadata["media_processed"] = True
    return state


async def _process_audio(state: AgentState) -> AgentState:
    """
    Processa áudio para transcrição.

    Implementação real deve chamar audio_processing_service.
    Por enquanto, usa transcrição já fornecida se existir.
    """
    # Se já tem transcrição (veio do request), usar
    if state.media_transcription:
        logger.debug("Usando transcrição existente")
        return state

    # TODO: Implementar chamada real para serviço de transcrição
    # Exemplo:
    # from app.services.audio_processing_service import transcribe_audio
    # transcription = await transcribe_audio(state.media_url)
    # state.media_transcription = transcription

    state.media_transcription = "[Transcrição não disponível - implementar serviço]"
    logger.warning("Transcrição não implementada ainda")
    return state


async def _process_image(state: AgentState) -> AgentState:
    """
    Processa imagem para análise.

    Implementação real deve chamar image_processing_service.
    Por enquanto, usa análise já fornecida se existir.
    """
    # Se já tem análise (veio do request), usar
    if state.media_analysis:
        logger.debug("Usando análise existente")
        return state

    # TODO: Implementar chamada real para serviço de análise de imagem
    # Exemplo:
    # from app.services.image_processing_service import analyze_image
    # analysis = await analyze_image(state.media_url)
    # state.media_analysis = analysis

    state.media_analysis = "[Análise não disponível - implementar serviço]"
    logger.warning("Análise de imagem não implementada ainda")
    return state
