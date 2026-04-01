"""Cliente OpenAI."""

from functools import lru_cache

from openai import AsyncOpenAI

from app.config.settings import get_settings

settings = get_settings()


@lru_cache
def get_openai_client() -> AsyncOpenAI:
    """Retorna cliente OpenAI cacheado."""
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY deve estar configurada no .env")

    return AsyncOpenAI(api_key=settings.openai_api_key)
