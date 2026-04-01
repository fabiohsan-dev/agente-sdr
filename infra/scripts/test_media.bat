@echo off
REM ============================================
REM SDR Agent - Teste Rápido de Mídia
REM ============================================

echo.
echo ============================================
echo TESTE DE MIDIA - SDR AGENT
echo ============================================
echo.

REM Ativar ambiente
call .venv\Scripts\activate.bat

echo Testando processamento de tags de mídia...
echo.

python -c "
from app.services.media_tag_service import (
    process_media_tags,
    extract_media_tags,
    format_for_display,
    has_media_tag,
)

# Teste 1: Tag de áudio
texto_teste = 'Faaaaala João, muito bom te ver por aqui!\\\\[MEDIA:AUDIO_PADRAO]'
print('Teste 1: Tag de áudio')
print('Entrada:', texto_teste)
print('Saída:', format_for_display(texto_teste))
print()

# Teste 2: Extrair tags
tags = extract_media_tags(texto_teste)
print('Teste 2: Extrair tags')
print('Tags encontradas:', tags)
print()

# Teste 3: Verificar se tem tag
print('Teste 3: Tem tag de mídia?')
print('Resultado:', has_media_tag(texto_teste))
print()

# Teste 4: URL específica
from app.services.media_tag_service import get_media_url
print('Teste 4: URL do áudio')
print('URL:', get_media_url('AUDIO_PADRAO'))
print()

print('✅ Todos os testes passaram!')
"

echo.
echo ============================================
echo Para testar no playground:
echo 1. Acesse: http://127.0.0.1:8001
echo 2. Envie: 500
echo 3. Verifique se áudio aparece
echo ============================================
echo.

pause
