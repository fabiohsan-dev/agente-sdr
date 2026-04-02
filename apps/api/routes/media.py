"""Rota de mídia."""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.chat import MediaRequest, MediaResponse
from app.services.audio_processing_service import get_audio_processing_service
from app.services.image_processing_service import get_image_processing_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["Media"])


@router.post("/process", response_model=MediaResponse)
async def process_media(request: MediaRequest) -> MediaResponse:
    """
    Processa arquivo de mídia (áudio ou imagem).

    Para áudio: realiza transcrição
    Para imagem: realiza análise

    Args:
        request: Request com URL da mídia e tipo

    Returns:
        Resultado do processamento
    """
    logger.info(f"Processando mídia: {request.media_type} - {request.media_url}")

    # media_repo = MediaAssetsRepository()

    # ============================================
    # CRIAR MEDIA ASSET
    # ============================================

    from uuid import uuid4

    media_id = uuid4()

    # Criar registro no banco (sem lead_id por enquanto)
    # Em produção, você associaria com um lead específico
    # asset_data = {
    #     "id": media_id,
    #     "media_type": request.media_type,
    #     "cdn_url": request.media_url,
    #     "mime_type": request.mime_type,
    #     "original_filename": request.filename,
    # }

    # ============================================
    # PROCESSAR DE ACORDO COM O TIPO
    # ============================================

    transcription = None
    analysis = None
    status = "pending"

    try:
        if request.media_type == "audio":
            # Processar áudio
            audio_service = get_audio_processing_service()
            transcription = await audio_service.transcribe_audio_url(request.media_url)
            status = "completed" if transcription else "failed"
            logger.info(
                f"Áudio transcrito: {len(transcription) if transcription else 0} caracteres"
            )

        elif request.media_type == "image":
            # Processar imagem
            image_service = get_image_processing_service()
            analysis = await image_service.analyze_image_url(request.media_url)
            status = "completed" if analysis else "failed"
            logger.info(f"Imagem analisada: {len(analysis) if analysis else 0} caracteres")

        else:
            raise HTTPException(
                status_code=400, detail=f"Tipo de mídia não suportado: {request.media_type}"
            )

    except Exception as e:
        logger.error(f"Erro no processamento de mídia: {e}")
        status = "failed"

    # ============================================
    # ATUALIZAR MEDIA ASSET
    # ============================================

    # Nota: Em produção, salvaria no banco corretamente
    # await media_repo.update_status(media_id, status, transcription, analysis)

    # ============================================
    # RETORNAR RESULTADO
    # ============================================

    return MediaResponse(
        media_id=media_id,
        status=status,
        transcription=transcription,
        analysis=analysis,
        cdn_url=request.media_url,
    )


@router.post("/transcribe")
async def transcribe_audio(
    audio_url: str,
):
    """
    Transcreve arquivo de áudio.

    Args:
        audio_url: URL do arquivo de áudio

    Returns:
        Transcrição
    """
    audio_service = get_audio_processing_service()
    transcription = await audio_service.transcribe_audio_url(audio_url)

    if not transcription:
        raise HTTPException(status_code=500, detail="Falha na transcrição")

    return {"transcription": transcription}


@router.post("/analyze")
async def analyze_image(
    image_url: str,
    prompt: str | None = None,
):
    """
    Analisa imagem.

    Args:
        image_url: URL da imagem
        prompt: Prompt específico (opcional)

    Returns:
        Análise da imagem
    """
    image_service = get_image_processing_service()
    analysis = await image_service.analyze_image_url(image_url, prompt)

    if not analysis:
        raise HTTPException(status_code=500, detail="Falha na análise")

    return {"analysis": analysis}
