"""Serviço de processamento de imagem - análise com visão computacional."""

import logging

from app.config.settings import get_settings
from app.integrations.openai.client import get_openai_client
from app.services.media_download_service import get_media_download_service

logger = logging.getLogger(__name__)

settings = get_settings()


class ImageProcessingService:
    """Serviço para processamento de imagem (análise com visão computacional)."""

    def __init__(self):
        self.openai_client = get_openai_client()
        self.download_service = get_media_download_service()

    async def analyze_image_url(
        self,
        image_url: str,
        prompt: str | None = None,
    ) -> str | None:
        """
        Analisa imagem de uma URL.

        Args:
            image_url: URL da imagem
            prompt: Prompt específico para análise (opcional)

        Returns:
            Análise da imagem ou None
        """
        # Usar GPT-4 Vision para análise
        return await self._analyze_with_vision(image_url, prompt)

    async def analyze_image_bytes(
        self,
        image_content: bytes,
        mime_type: str = "image/jpeg",
        prompt: str | None = None,
    ) -> str | None:
        """
        Analisa imagem em bytes.

        Args:
            image_content: Conteúdo da imagem em bytes
            mime_type: MIME type da imagem
            prompt: Prompt específico para análise (opcional)

        Returns:
            Análise da imagem ou None
        """
        import base64

        # Codificar para base64
        base64_image = base64.b64encode(image_content).decode("utf-8")
        data_url = f"data:{mime_type};base64,{base64_image}"

        return await self._analyze_with_vision(data_url, prompt)

    async def _analyze_with_vision(
        self,
        image_source: str,  # URL ou data_url
        prompt: str | None = None,
    ) -> str | None:
        """
        Analisa imagem usando GPT-4 Vision.

        Args:
            image_source: URL ou data_url da imagem
            prompt: Prompt específico (opcional)

        Returns:
            Análise da imagem ou None
        """
        try:
            # Prompt padrão de análise
            analysis_prompt = prompt or (
                "Analise esta imagem em detalhes. Descreva:\n"
                "1. O que está na imagem\n"
                "2. Contexto ou cenário\n"
                "3. Qualquer texto visível\n"
                "4. Elementos relevantes\n\n"
                "Seja conciso mas informativo."
            )

            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
            )

            response = await llm.ainvoke(
                [
                    (
                        "human",
                        [
                            {"type": "text", "text": analysis_prompt},
                            {"type": "image_url", "image_url": {"url": image_source}},
                        ],
                    ),
                ]
            )

            result = response.content
            logger.info(f"Imagem analisada: {len(result)} caracteres")
            return result

        except Exception as e:
            logger.error(f"Erro na análise de imagem: {e}")
            return None

    async def extract_text_from_image(
        self,
        image_url: str,
    ) -> str | None:
        """
        Extrai texto de imagem (OCR).

        Args:
            image_url: URL da imagem

        Returns:
            Texto extraído ou None
        """
        prompt = "Extraia todo o texto visível nesta imagem. Se não houver texto, responda 'Nenhum texto visível'."
        return await self.analyze_image_url(image_url, prompt)

    async def describe_image_for_context(
        self,
        image_url: str,
    ) -> str | None:
        """
        Descreve imagem para contexto de conversa.

        Args:
            image_url: URL da imagem

        Returns:
            Descrição contextual ou None
        """
        prompt = (
            "Descreva esta imagem de forma concisa para contexto de uma conversa. "
            "Foque nos elementos mais importantes e relevantes. "
            "Máximo 3 frases."
        )
        return await self.analyze_image_url(image_url, prompt)


# Singleton
_image_processing_service: ImageProcessingService | None = None


def get_image_processing_service() -> ImageProcessingService:
    """Retorna instância singleton do ImageProcessingService."""
    global _image_processing_service
    if _image_processing_service is None:
        _image_processing_service = ImageProcessingService()
    return _image_processing_service
