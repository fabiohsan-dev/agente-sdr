"""Dependencies da API."""

from functools import lru_cache

from app.config.settings import Settings, get_settings


def get_settings_dep() -> Settings:
    """Dependency para settings."""
    return get_settings()


@lru_cache
def get_settings_cached() -> Settings:
    """Dependency cacheado para settings."""
    return get_settings()
