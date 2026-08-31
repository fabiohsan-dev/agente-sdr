"""Parser de mensagens no formato Chatwoot/n8n.

Este parser processa respostas do LLM e extrai:
- Texto limpo
- Mídias (áudio, imagem)
- Metadados

Formato esperado:
```
Faaaaala João, muito bom te ver por aqui!
\\
[MEDIA:AUDIO_PADRAO]
```

Saída:
```json
{
  "text": "Faaaaala João, muito bom te ver por aqui!",
  "media": [
    {
      "type": "audio",
      "url": "https://sdr-w.agenciaalea.com.br/audio-w-padrao.m4a"
    }
  ]
}
```
"""

import logging
import re
from typing import TypedDict

logger = logging.getLogger(__name__)


class MediaItem(TypedDict):
    """Item de mídia."""

    type: str  # audio, image
    url: str
    name: str


class ParsedMessage(TypedDict):
    """Mensagem processada."""

    text: str
    media: list[MediaItem]


def get_media_urls() -> dict[str, str]:
    """Retorna dicionário de URLs de mídia dinâmicas a partir das configurações."""
    try:
        from app.config.settings import get_settings

        settings = get_settings()
        return {
            "AUDIO_PADRAO": settings.audio_padrao_url
            or "https://sdr-w.agenciaalea.com.br/audio-w-padrao.m4a",
            "CASE_GENERICO": settings.case_generico_url
            or "https://sdr-w.agenciaalea.com.br/case-sergio.png",
        }
    except Exception:
        return {
            "AUDIO_PADRAO": "https://sdr-w.agenciaalea.com.br/audio-w-padrao.m4a",
            "CASE_GENERICO": "https://sdr-w.agenciaalea.com.br/case-sergio.png",
        }


# URLs padrão das mídias (fallback e retrocompatibilidade)
MEDIA_URLS = get_media_urls()

# Padrão regex para encontrar tags
MEDIA_TAG_PATTERN = re.compile(r"\[MEDIA:(\w+)\]")


def parse_message(text: str) -> ParsedMessage:
    """
    Processa mensagem e extrai texto + mídias.

    Args:
        text: Texto cru do LLM (pode conter tags e separadores)

    Returns:
        Dict com texto limpo e lista de mídias
    """
    if not text:
        return {"text": "", "media": []}

    result_text = text
    media_items: list[MediaItem] = []

    # 1. Encontrar todas as tags de mídia
    tags_found = MEDIA_TAG_PATTERN.findall(text)

    for tag_name in tags_found:
        if tag_name in MEDIA_URLS:
            media_type = "audio" if tag_name == "AUDIO_PADRAO" else "image"
            media_items.append(
                {
                    "type": media_type,
                    "url": MEDIA_URLS[tag_name],
                    "name": tag_name,
                }
            )
            # Remover tag do texto
            result_text = result_text.replace(f"[MEDIA:{tag_name}]", "")

    # 2. Limpar texto
    # Remover separadores \\
    result_text = result_text.replace("\\\\", "\n")
    result_text = result_text.replace("\\", "\n")

    # Remover linhas vazias extras
    lines = [line.strip() for line in result_text.split("\n") if line.strip()]
    result_text = "\n".join(lines)

    return {
        "text": result_text,
        "media": media_items,
    }


def parse_for_chatwoot(text: str) -> dict:
    """
    Processa mensagem para formato Chatwoot.

    Similar ao parse_message mas retorna no formato que o n8n envia para Chatwoot.

    Args:
        text: Texto cru do LLM

    Returns:
        Dict no formato Chatwoot
    """
    parsed = parse_message(text)

    return {
        "content": parsed["text"],
        "media": parsed["media"],
        "private": False,
    }


def has_media(text: str) -> bool:
    """
    Verifica se texto contém tags de mídia.

    Args:
        text: Texto para verificar

    Returns:
        True se contém mídia
    """
    return bool(MEDIA_TAG_PATTERN.search(text))


def extract_media_urls(text: str) -> list[str]:
    """
    Extrai apenas URLs das mídias.

    Args:
        text: Texto com tags

    Returns:
        Lista de URLs
    """
    parsed = parse_message(text)
    return [m["url"] for m in parsed["media"]]


def clean_text(text: str) -> str:
    """
    Limpa texto removendo tags e separadores.

    Args:
        text: Texto cru do LLM

    Returns:
        Texto limpo
    """
    parsed = parse_message(text)
    return parsed["text"]
