"""Servidor do Playground."""

import logging
from pathlib import Path

import jinja2
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ============================================
# CARREGAR .ENV EXPLICITAMENTE
# ============================================

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, encoding="utf-8")

from app.config.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# ============================================
# CRIAR APP
# ============================================

app = FastAPI(
    title="SDR Agent Playground",
    description="Playground para testar o SDR Agent",
    version="0.1.0",
)

# ============================================
# SETUP PATHS
# ============================================

BASE_DIR = Path(__file__).parent
# Python 3.14 fix: desabilitar cache LRU do Jinja2 (bug de compatibilidade)
_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(BASE_DIR / "templates")),
    auto_reload=True,
    cache_size=0,
)
templates = Jinja2Templates(env=_jinja_env)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# ============================================
# ROUTES
# ============================================


@app.get("/", response_class=HTMLResponse)
async def playground(request: Request):
    """Página principal do playground."""
    return templates.TemplateResponse(request=request, name="chat.html")


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok"}


# ============================================
# RUN
# ============================================


if __name__ == "__main__":
    import uvicorn

    from app.config.settings import get_settings

    settings = get_settings()

    uvicorn.run(
        "server:app",
        host=settings.playground_host,
        port=settings.playground_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
