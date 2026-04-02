# ============================================
# SDR Agent — Dockerfile
# ============================================
# Multi-stage build: compila dependências em stage separado
# Imagem final ~200MB (python:3.12-slim)

# ── Stage 1: Build ──────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Instalar dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar pyproject primeiro para cache de deps
COPY pyproject.toml ./
COPY README.md ./

# Criar estrutura mínima para pip install funcionar
# (hatchling precisa dos packages referenciados)
COPY app/ ./app/
COPY apps/ ./apps/

# Instalar dependências em um virtual env isolado
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[prod]"

# ── Stage 2: Runtime ────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copiar venv do builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copiar código da aplicação
COPY app/ ./app/
COPY apps/ ./apps/
COPY langgraph.json ./
COPY pyproject.toml ./

# Criar diretório de logs
RUN mkdir -p /app/logs

# Criar usuário não-root
RUN groupadd -r sdr && useradd -r -g sdr -d /app -s /sbin/nologin sdr
RUN chown -R sdr:sdr /app
USER sdr

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health'); r.raise_for_status()"

# Expor porta da API
EXPOSE 8000

# Entrypoint: uvicorn com workers otimizado para produção
# uvloop é instalado via [prod] e melhora performance 2-4x
CMD ["uvicorn", "apps.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--loop", "uvloop", \
     "--access-log"]
