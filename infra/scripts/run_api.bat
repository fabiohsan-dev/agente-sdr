@echo off
REM ============================================
REM SDR Agent - Rodar API (Windows)
REM ============================================

echo.
echo ============================================
echo SDR Agent - Iniciando API
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

REM Rodar API
echo Iniciando API em http://127.0.0.1:8000
echo Documentacao: http://127.0.0.1:8000/docs
echo.

cd apps\api
uvicorn main:app --host 127.0.0.1 --port 8000 --reload

pause
