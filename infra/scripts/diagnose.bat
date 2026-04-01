@echo off
REM ============================================
REM SDR Agent - Diagnóstico Completo
REM ============================================

echo.
echo ============================================
echo DIAGNOSTICO - SDR AGENT
echo ============================================
echo.

REM Ativar ambiente
call .venv\Scripts\activate.bat

echo 1. Verificando variaveis de ambiente...
echo.

python infra/scripts/check_settings.py

echo.
echo 2. Testando conexao OpenAI...
echo.

python infra\scripts\test_openai.py

echo.
echo 3. Verificando arquivos de prompt...
echo.

if exist app\agent\prompts\system.md (
    echo   ✅ system.md existe
) else (
    echo   ❌ system.md NAO existe
)

if exist app\agent\prompts\rules.md (
    echo   ✅ rules.md existe
) else (
    echo   ❌ rules.md NAO existe
)

if exist app\agent\prompts\stages.md (
    echo   ✅ stages.md existe
) else (
    echo   ❌ stages.md NAO existe
)

if exist app\agent\prompts\media.md (
    echo   ✅ media.md existe
) else (
    echo   ❌ media.md NAO existe
)

echo.
echo 4. Verificando servicos...
echo.

if exist app\services\media_tag_service.py (
    echo   ✅ media_tag_service.py existe
) else (
    echo   ❌ media_tag_service.py NAO existe
)

echo.
echo ============================================
echo PROXIMOS PASSOS:
echo.
echo Se algum item estiver ❌, corrija antes de continuar.
echo.
echo Para testar o agente:
echo 1. infra\scripts\run_api.bat
echo 2. infra\scripts\run_playground.bat
echo 3. Acesse http://127.0.0.1:8001
echo 4. Envie: 500
echo ============================================
echo.

pause
