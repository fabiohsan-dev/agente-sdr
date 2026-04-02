"""API FastAPI principal."""

import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ============================================
# CARREGAR .ENV EXPLICITAMENTE
# ============================================
# Isso garante que .env seja carregado antes de qualquer import

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, encoding="utf-8")

from app.config.logging import setup_logging  # noqa: E402
from app.config.settings import get_settings  # noqa: E402
from apps.api.routes import chat, health, media, metrics, webhook  # noqa: E402

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()

# ============================================
# CRIAR APP
# ============================================

app = FastAPI(
    title="SDR Agent API",
    description="API para agente SDR com LangGraph",
    version="0.1.0",
)

# ============================================
# MIDDLEWARE
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# INCLUDE ROUTERS
# ============================================

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(media.router)
app.include_router(webhook.router)
app.include_router(metrics.router)

# ============================================
# STATIC FILES
# ============================================

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ============================================
# HEALTH CHECKS
# ============================================


@app.on_event("startup")
async def startup_event():
    """Evento de startup da API."""
    logger.info(f"SDR Agent API iniciando em {settings.api_host}:{settings.api_port}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Langfuse enabled: {settings.langfuse_enabled}")
    logger.info(f"Cal.com enabled: {settings.calcom_enabled}")
    logger.info(f"Chatwoot enabled: {settings.chatwoot_enabled}")
    logger.info(f"Dashboard: http://{settings.api_host}:{settings.api_port}/metrics/dashboard")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de shutdown da API."""
    logger.info("SDR Agent API encerrando")


# ============================================
# ROOT
# ============================================


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "SDR Agent API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "dashboard": "/metrics/dashboard",
        "webhook_chatwoot": "/webhook/chatwoot",
    }


# ============================================
# RUN
# ============================================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
