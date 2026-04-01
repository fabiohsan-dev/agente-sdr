@echo off
REM ============================================
REM SDR Agent - Rodar Playground (Windows)
REM ============================================

echo.
echo ============================================
echo SDR Agent - Iniciando Playground
echo ============================================
echo.

REM Verificar se .venv existe
if not exist .venv (
    echo ERRO: Ambiente virtual nao encontrado.
    echo Execute setup.bat primeiro.
    pause
    exit /b 1
)

REM Ativar ambiente virtual
call .venv\Scripts\activate.bat

REM Rodar Playground
echo Iniciando Playground em http://127.0.0.1:8001
echo.

cd apps\playground
uvicorn server:app --host 127.0.0.1 --port 8001 --reload

pause
