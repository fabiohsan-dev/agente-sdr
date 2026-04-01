@echo off
REM ============================================
REM SDR Agent - Configuração Inicial (Windows)
REM ============================================

echo.
echo ============================================
echo SDR AGENT - CONFIGURACAO INICIAL
echo ============================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado. Instale Python 3.11+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/6] Python encontrado
echo.

REM Verificar se .venv existe
if exist .venv (
    echo [2/6] Ambiente virtual ja existe
) else (
    echo [2/6] Criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo ERRO: Falha ao criar ambiente virtual
        pause
        exit /b 1
    )
)
echo.

REM Ativar ambiente virtual
call .venv\Scripts\activate.bat

REM Verificar se .env existe
if exist .env (
    echo [3/6] Arquivo .env ja existe
) else (
    echo [3/6] Copiando .env.example para .env...
    copy .env.example .env
    echo.
    echo AVISO: .env criado. Voce precisa configurar as chaves.
)
echo.

REM Gerar segredos internos (modo não-interativo)
echo [4/6] Gerando segredos internos...
python infra\scripts\generate_secrets.py <nul 2>&1
echo.

REM Instalar dependencias (com tratamento de erro)
echo [5/6] Instalando dependencias...
python -m pip install --upgrade pip --quiet 2>&1
pip install -e . --quiet 2>&1
if errorlevel 1 (
    echo.
    echo AVISO: Falha ao instalar algumas dependencias.
    echo Tentando instalar novamente...
    echo.
    pip install fastapi uvicorn python-multipart jinja2 pydantic pydantic-settings python-dotenv --quiet 2>&1
    pip install langgraph langchain langchain-openai langchain-core --quiet 2>&1
    pip install supabase httpx --quiet 2>&1
    pip install langfuse openai --quiet 2>&1
    pip install pytest pytest-asyncio pytest-cov --quiet 2>&1
)
echo.

REM Verificar configuracoes
echo [6/6] Verificando configuracoes...
echo.
python -c "from app.config.settings import check_settings; check_settings()" 2>&1
echo.

echo ============================================
echo CONFIGURACAO CONCLUIDA!
echo ============================================
echo.
echo PROXIMOS PASSOS:
echo.
echo 1. Edite o arquivo .env e configure:
echo    - OPENAI_API_KEY (obrigatorio)
echo    - SUPABASE_URL (obrigatorio)
echo    - SUPABASE_SERVICE_ROLE_KEY (obrigatorio)
echo.
echo 2. No Supabase, execute o schema.sql:
echo    - Acesse https://app.supabase.com
echo    - Va em SQL Editor
echo    - Copie e execute infra\sql\schema.sql
echo.
echo 3. Para rodar o projeto:
echo    - API:        infra\scripts\run_api.bat
echo    - Playground: infra\scripts\run_playground.bat
echo.
echo ============================================
echo.

pause
