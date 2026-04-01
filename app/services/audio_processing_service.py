"""Serviço de processamento de áudio - transcrição."""

import logging
from pathlib import Path

from app.config.settings import get_settings
from app.integrations.openai.client import get_openai_client
from app.services.media_download_service import get_media_download_service

logger = logging.getLogger(__name__)

settings = get_settings()


class AudioProcessingService:
    """Serviço para processamento de áudio (transcrição)."""

    def __init__(self):
        self.openai_client = get_openai_client()
        self.download_service = get_media_download_service()

    async def transcribe_audio_url(
        self,
        audio_url: str,
    ) -> str | None:
        """
        Transcreve áudio de uma URL.

        Args:
            audio_url: URL do arquivo de áudio

        Returns:
            Transcrição ou None
        """
        # Baixar áudio
        audio_content = await self.download_service.download_audio(audio_url)
        if not audio_content:
            logger.error("Falha ao baixar áudio para transcrição")
            return None

        # Transcrever
        return await self._transcribe_audio_bytes(audio_content)

    async def transcribe_audio_file(
        self,
        file_path: Path,
    ) -> str | None:
        """
        Transcreve arquivo de áudio local.

        Args:
            file_path: Caminho do arquivo de áudio

        Returns:
            Transcrição ou None
        """
        if not file_path.exists():
            logger.error(f"Arquivo não encontrado: {file_path}")
            return None

        audio_content = file_path.read_bytes()
        return await self._transcribe_audio_bytes(audio_content)

    async def _transcribe_audio_bytes(
        self,
        audio_content: bytes,
    ) -> str | None:
        """
        Transcreve bytes de áudio.

        Args:
            audio_content: Conteúdo do áudio em bytes

        Returns:
            Transcrição ou None
        """
        try:
            # Usar Whisper API
            from io import BytesIO

            audio_file = BytesIO(audio_content)
            audio_file.name = "audio.mp3"  # Whisper precisa de nome

            transcription = await self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pt",  # Português
            )

            result = transcription.text
            logger.info(f"Áudio transcrito: {len(result)} caracteres")
            return result

        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")
            return None

    async def transcribe_with_timestamps(
        self,
        audio_url: str,
    ) -> dict | None:
        """
        Transcreve áudio com timestamps.

        Args:
            audio_url: URL do arquivo de áudio

        Returns:
            Dict com transcription e segments (timestamps) ou None
        """
        audio_content = await self.download_service.download_audio(audio_url)
        if not audio_content:
            return None

        try:
            from io import BytesIO

            audio_file = BytesIO(audio_content)
            audio_file.name = "audio.mp3"

            # Transcrição com timestamps
            transcription = await self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pt",
                timestamp_granularities=["segment"],
                response_format="verbose_json",
            )

            result = {
                "transcription": transcription.text,
                "segments": transcription.segments if hasattr(transcription, "segments") else [],
            }

            logger.info(f"Áudio transcrito com timestamps: {len(result['transcription'])} caracteres")
            return result

        except Exception as e:
            logger.error(f"Erro na transcrição com timestamps: {e}")
            return None


# Singleton
_audio_processing_service: AudioProcessingService | None = None


def get_audio_processing_service() -> AudioProcessingService:
    """Retorna instância singleton do AudioProcessingService."""
    global _audio_processing_service
    if _audio_processing_service is None:
        _audio_processing_service = AudioProcessingService()
    return _audio_processing_service
