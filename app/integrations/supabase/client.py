"""Cliente Supabase."""

from functools import lru_cache

from supabase import Client, create_client

from app.config.settings import get_settings

settings = get_settings()


@lru_cache
def get_supabase_client() -> Client:
    """Retorna cliente Supabase cacheado."""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise ValueError(
            "SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY devem estar configuradas no .env"
        )

    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return client
