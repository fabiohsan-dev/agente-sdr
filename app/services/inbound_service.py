"""Serviço de inbound - processa mensagens recebidas."""

import logging
from uuid import UUID

from app.domain.enums import MessageType
from app.repositories.messages_repository import MessagesRepository

logger = logging.getLogger(__name__)


class InboundService:
    """Serviço para processamento de mensagens inbound."""

    def __init__(self):
        self.messages_repo = MessagesRepository()

    async def process_text_message(
        self,
        conversation_id: UUID,
        content: str,
    ) -> dict:
        """
        Processa mensagem de texto recebida.

        Args:
            conversation_id: ID da conversation
            content: Conteúdo da mensagem

        Returns:
            Mensagem criada
        """
        message = await self.messages_repo.create_inbound_text(
            conversation_id=conversation_id,
            content=content,
        )

        logger.debug(f"Mensagem de texto processada: {message.id}")

        return {
            "message_id": str(message.id),
            "message_type": "text",
            "content": message.content,
        }

    async def process_media_message(
        self,
        conversation_id: UUID,
        media_url: str,
        media_type: MessageType,
        mime_type: str | None = None,
        filename: str | None = None,
        transcription: str | None = None,
        analysis: str | None = None,
    ) -> dict:
        """
        Processa mensagem de mídia recebida.

        Args:
            conversation_id: ID da conversation
            media_url: URL da mídia (CDN)
            media_type: Tipo de mídia (audio, image)
            mime_type: MIME type
            filename: Nome original do arquivo
            transcription: Transcrição (para áudio)
            analysis: Análise (para imagem)

        Returns:
            Mensagem criada
        """
        message = await self.messages_repo.create_inbound_media(
            conversation_id=conversation_id,
            media_url=media_url,
            media_type=media_type,
            media_mime_type=mime_type,
            media_filename=filename,
            transcription=transcription,
            analysis=analysis,
        )

        logger.debug(f"Mensagem de mídia processada: {message.id}")

        return {
            "message_id": str(message.id),
            "message_type": media_type.value,
            "media_url": media_url,
            "mime_type": mime_type,
            "filename": filename,
            "transcription": transcription,
            "analysis": analysis,
        }

    async def save_message_with_media(
        self,
        conversation_id: UUID,
        content: str | None,
        media_url: str,
        media_type: MessageType,
        mime_type: str | None = None,
        filename: str | None = None,
    ) -> dict:
        """
        Salva mensagem com mídia (texto + mídia).

        Args:
            conversation_id: ID da conversation
            content: Conteúdo de texto (opcional)
            media_url: URL da mídia
            media_type: Tipo de mídia
            mime_type: MIME type
            filename: Nome original do arquivo

        Returns:
            Mensagem criada
        """
        message = await self.messages_repo.create(
            conversation_id=conversation_id,
            direction="inbound",
            content=content,
            message_type=media_type,
            media_url=media_url,
            media_mime_type=mime_type,
            media_filename=filename,
        )

        logger.debug(f"Mensagem com mídia salva: {message.id}")

        return {
            "message_id": str(message.id),
            "message_type": media_type.value,
            "content": message.content,
            "media_url": media_url,
        }


# Singleton
_inbound_service: InboundService | None = None


def get_inbound_service() -> InboundService:
    """Retorna instância singleton do InboundService."""
    global _inbound_service
    if _inbound_service is None:
        _inbound_service = InboundService()
    return _inbound_service
