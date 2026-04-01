@echo off
REM ============================================
REM SDR Agent - Setup Inicial (Windows)
REM ============================================

echo.
echo ============================================
echo SDR Agent - Setup Inicial
echo ============================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado. Instale Python 3.11+
    pause
    exit /b 1
)

echo [1/5] Python encontrado
echo.

REM Criar ambiente virtual
echo [2/5] Criando ambiente virtual...
python -m venv .venv
if errorlevel 1 (
    echo ERRO: Falha ao criar ambiente virtual
    pause
    exit /b 1
)

echo [3/5] Ambiente virtual criado
echo.

REM Ativar ambiente virtual
echo [4/5] Ativando ambiente virtual e instalando dependencias...
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -e .

echo [5/5] Dependencias instaladas
echo.

REM Copiar .env.example se nao existir
if not exist .env (
    echo [INFO] Copiando .env.example para .env
    copy .env.example .env
    echo.
    echo ============================================
    echo IMPORTANTE: Configure o arquivo .env com:
    echo - OPENAI_API_KEY
    echo - SUPABASE_URL e SUPABASE_KEY
    echo - LANGFUSE_PUBLIC_KEY e LANGFUSE_SECRET_KEY (opcional)
    echo - CALCOM_API_KEY e CALCOM_EVENT_TYPE_ID (opcional)
    echo ============================================
    echo.
)

echo ============================================
echo Setup concluido!
echo.
echo Para rodar o projeto:
echo   1. Configure o arquivo .env
echo   2. Execute: run_api.bat (para API)
echo   3. Execute: run_playground.bat (para Playground)
echo ============================================
echo.

pause
