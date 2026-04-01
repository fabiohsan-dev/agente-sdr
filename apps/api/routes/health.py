"""Rota de health check com verificação real de dependências."""

import logging
import time

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
async def health_check():
    """Health check básico (para load balancers e Docker)."""
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check():
    """Readiness check com verificação de dependências externas."""
    checks = {}
    overall = True

    # ── Supabase ────────────────────────────
    try:
        from app.integrations.supabase.client import get_supabase_client

        client = get_supabase_client()
        start = time.time()
        client.table("leads").select("id").limit(1).execute()
        checks["supabase"] = {
            "status": "ok",
            "latency_ms": round((time.time() - start) * 1000),
        }
    except Exception as e:
        checks["supabase"] = {"status": "error", "error": str(e)[:100]}
        overall = False

    # ── OpenAI ──────────────────────────────
    try:
        from app.config.settings import get_settings

        settings = get_settings()
        checks["openai"] = {
            "status": "ok" if settings.openai_api_key else "not_configured",
            "model": settings.openai_model,
        }
    except Exception as e:
        checks["openai"] = {"status": "error", "error": str(e)[:100]}

    # ── Chatwoot ────────────────────────────
    try:
        from app.config.settings import get_settings

        settings = get_settings()
        checks["chatwoot"] = {
            "status": "ok" if settings.chatwoot_enabled else "not_configured",
        }
    except Exception:
        checks["chatwoot"] = {"status": "not_configured"}

    # ── Cal.com ─────────────────────────────
    try:
        from app.config.settings import get_settings

        settings = get_settings()
        checks["calcom"] = {
            "status": "ok" if settings.calcom_enabled else "not_configured",
        }
    except Exception:
        checks["calcom"] = {"status": "not_configured"}

    # ── Langfuse ────────────────────────────
    try:
        from app.config.settings import get_settings

        settings = get_settings()
        checks["langfuse"] = {
            "status": "ok" if settings.langfuse_enabled else "not_configured",
        }
    except Exception:
        checks["langfuse"] = {"status": "not_configured"}

    return {
        "status": "ready" if overall else "degraded",
        "checks": checks,
    }
