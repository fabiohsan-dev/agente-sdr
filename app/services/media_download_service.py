"""Serviço de download de mídia - baixa arquivos da CDN."""

import logging
from pathlib import Path

import httpx

from app.repositories.media_assets_repository import MediaAssetsRepository

logger = logging.getLogger(__name__)


class MediaDownloadService:
    """Serviço para download de arquivos de mídia da CDN."""

    def __init__(self):
        self.media_repo = MediaAssetsRepository()

    async def download_from_url(
        self,
        url: str,
        timeout: int = 30,
    ) -> bytes | None:
        """
        Baixa arquivo de uma URL.

        Args:
            url: URL do arquivo (CDN)
            timeout: Timeout em segundos

        Returns:
            Conteúdo do arquivo em bytes ou None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=timeout)
                response.raise_for_status()
                return response.content

        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao baixar mídia: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao baixar mídia: {e}")
            return None

    async def download_and_get_info(
        self,
        url: str,
    ) -> dict | None:
        """
        Baixa arquivo e retorna informações.

        Args:
            url: URL do arquivo

        Returns:
            Dict com content, mime_type, size ou None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30)
                response.raise_for_status()

                content = response.content
                mime_type = response.headers.get("content-type", "application/octet-stream")
                size = len(content)

                return {
                    "content": content,
                    "mime_type": mime_type,
                    "size": size,
                    "url": url,
                }

        except Exception as e:
            logger.error(f"Erro ao baixar e obter info: {e}")
            return None

    async def save_temporarily(
        self,
        url: str,
        filename: str | None = None,
        temp_dir: str = "temp",
    ) -> Path | None:
        """
        Baixa arquivo e salva temporariamente.

        Args:
            url: URL do arquivo
            filename: Nome do arquivo (gera UUID se None)
            temp_dir: Diretório temporário

        Returns:
            Caminho do arquivo ou None
        """
        content = await self.download_from_url(url)
        if not content:
            return None

        # Criar diretório temporário
        temp_path = Path(temp_dir)
        temp_path.mkdir(exist_ok=True)

        # Gerar nome do arquivo
        if not filename:
            import uuid

            filename = f"{uuid.uuid4()}.bin"

        file_path = temp_path / filename

        # Salvar arquivo
        file_path.write_bytes(content)
        logger.info(f"Arquivo salvo temporariamente: {file_path}")

        return file_path

    async def download_audio(
        self,
        url: str,
    ) -> bytes | None:
        """
        Baixa arquivo de áudio.

        Args:
            url: URL do áudio

        Returns:
            Conteúdo em bytes ou None
        """
        logger.info(f"Baixando áudio: {url}")
        return await self.download_from_url(url)

    async def download_image(
        self,
        url: str,
    ) -> bytes | None:
        """
        Baixa arquivo de imagem.

        Args:
            url: URL da imagem

        Returns:
            Conteúdo em bytes ou None
        """
        logger.info(f"Baixando imagem: {url}")
        return await self.download_from_url(url)


# Singleton
_media_download_service: MediaDownloadService | None = None


def get_media_download_service() -> MediaDownloadService:
    """Retorna instância singleton do MediaDownloadService."""
    global _media_download_service
    if _media_download_service is None:
        _media_download_service = MediaDownloadService()
    return _media_download_service
