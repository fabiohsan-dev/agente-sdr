"""Middleware e dependências de multi-tenancy.

Resolve o tenant a partir do header X-API-Key ou do payload Chatwoot.
Injeta tenant_id no contexto da request para uso nos repositórios.
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request

from app.integrations.supabase.client import get_supabase_client

logger = logging.getLogger(__name__)

# Cache simples em memória para evitar query a cada request
_tenant_cache: dict[str, dict[str, Any]] = {}


class TenantContext:
    """Contexto do tenant resolvido."""

    def __init__(
        self,
        tenant_id: UUID,
        name: str,
        slug: str,
        settings: dict[str, Any],
        is_active: bool = True,
    ):
        self.tenant_id = tenant_id
        self.name = name
        self.slug = slug
        self.settings = settings
        self.is_active = is_active

    @property
    def calcom_api_key(self) -> str | None:
        """Cal.com API key do tenant."""
        return self.settings.get("calcom_api_key")

    @property
    def calcom_event_type_id(self) -> int | None:
        """Cal.com event type do tenant."""
        return self.settings.get("calcom_event_type_id")

    @property
    def chatwoot_account_id(self) -> int | None:
        """Chatwoot account ID do tenant."""
        return self.settings.get("chatwoot_account_id")

    @property
    def chatwoot_inbox_id(self) -> int | None:
        """Chatwoot inbox ID do tenant."""
        return self.settings.get("chatwoot_inbox_id")

    @property
    def chatwoot_api_token(self) -> str | None:
        """Chatwoot API token do tenant."""
        return self.settings.get("chatwoot_api_token")

    @property
    def openai_model(self) -> str | None:
        """Modelo OpenAI override do tenant."""
        return self.settings.get("openai_model")

    @property
    def timezone(self) -> str:
        """Timezone do tenant."""
        return self.settings.get("timezone", "America/Sao_Paulo")

    @property
    def custom_prompt_override(self) -> str | None:
        """Override de prompt do tenant (ex: tom de voz diferente)."""
        return self.settings.get("custom_prompt_override")


async def resolve_tenant_by_api_key(api_key: str) -> TenantContext | None:
    """Resolve tenant a partir da API key.

    Returns:
        TenantContext ou None se não encontrado.
    """
    # Checar cache
    if api_key in _tenant_cache:
        cached = _tenant_cache[api_key]
        return TenantContext(
            tenant_id=UUID(cached["id"]),
            name=cached["name"],
            slug=cached["slug"],
            settings=cached.get("settings", {}),
            is_active=cached.get("is_active", True),
        )

    try:
        client = get_supabase_client()
        result = (
            client.table("tenants")
            .select("id, name, slug, settings, is_active")
            .eq("api_key", api_key)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )

        if not result.data:
            return None

        tenant_data = result.data[0]
        _tenant_cache[api_key] = tenant_data

        return TenantContext(
            tenant_id=UUID(tenant_data["id"]),
            name=tenant_data["name"],
            slug=tenant_data["slug"],
            settings=tenant_data.get("settings", {}),
            is_active=tenant_data.get("is_active", True),
        )

    except Exception as e:
        logger.error(f"Erro ao resolver tenant: {e}")
        return None


async def resolve_tenant_by_chatwoot_account(
    account_id: int,
) -> TenantContext | None:
    """Resolve tenant pelo Chatwoot account_id (busca no settings JSON)."""
    try:
        client = get_supabase_client()
        # Busca tenants com chatwoot_account_id no JSON de settings
        result = (
            client.table("tenants")
            .select("id, name, slug, settings, is_active, api_key")
            .eq("is_active", True)
            .execute()
        )

        for tenant_data in result.data or []:
            settings = tenant_data.get("settings", {})
            if settings.get("chatwoot_account_id") == account_id:
                # Cachear também
                _tenant_cache[tenant_data["api_key"]] = tenant_data
                return TenantContext(
                    tenant_id=UUID(tenant_data["id"]),
                    name=tenant_data["name"],
                    slug=tenant_data["slug"],
                    settings=settings,
                    is_active=True,
                )

        return None

    except Exception as e:
        logger.error(f"Erro ao resolver tenant por Chatwoot account: {e}")
        return None


def clear_tenant_cache():
    """Limpa cache de tenants (útil após alterações)."""
    global _tenant_cache
    _tenant_cache.clear()


# ── FastAPI Dependencies ────────────────────────────────────


async def get_tenant_optional(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> TenantContext | None:
    """Dependency opcional: resolve tenant se API key presente.

    Se não houver header X-API-Key, retorna None (modo single-tenant).
    Útil para rotas que funcionam com e sem multi-tenancy.
    """
    if not x_api_key:
        return None

    tenant = await resolve_tenant_by_api_key(x_api_key)
    if not tenant:
        raise HTTPException(
            status_code=401,
            detail="API key inválida ou tenant desativado",
        )

    return tenant


async def get_tenant_required(
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> TenantContext:
    """Dependency obrigatória: exige API key válida.

    Usar em rotas que DEVEM ter tenant (ex: criação de leads).
    """
    tenant = await resolve_tenant_by_api_key(x_api_key)
    if not tenant:
        raise HTTPException(
            status_code=401,
            detail="API key inválida ou tenant desativado. "
            "Inclua o header X-API-Key com uma chave válida.",
        )

    return tenant
