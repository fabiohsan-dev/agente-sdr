@echo off
REM ============================================
REM SDR Agent - Instalação Simples (Windows)
REM ============================================
REM Use este script se o configure.bat falhar

echo.
echo ============================================
echo SDR AGENT - INSTALACAO MANUAL
echo ============================================
echo.

REM Ativar ambiente virtual
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo ERRO: Ambiente virtual nao encontrado.
    echo Execute primeiro: python -m venv .venv
    pause
    exit /b 1
)

echo Instalando dependencias basicas...
echo.

REM Instalar pip mais recente
python -m pip install --upgrade pip

echo.
echo Instalando pacotes basicos...
pip install fastapi uvicorn[standard] python-multipart jinja2
pip install pydantic pydantic-settings python-dotenv
pip install httpx
pip install openai
pip install langchain langchain-core langchain-openai langgraph
pip install supabase
pip install langfuse
pip install pytest pytest-asyncio

echo.
echo ============================================
echo INSTALACAO CONCLUIDA!
echo ============================================
echo.
echo Agora edite o arquivo .env e configure:
echo   - OPENAI_API_KEY
echo   - SUPABASE_URL
echo   - SUPABASE_SERVICE_ROLE_KEY
echo.
echo Depois execute:
echo   infra\scripts\run_api.bat
echo.

pause
