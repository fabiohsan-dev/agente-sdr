"""Serviço para processamento de tags de mídia.

Compatível com parser do n8n/Chatwoot.
"""

import logging
from app.services.message_parser import parse_message, parse_for_chatwoot

logger = logging.getLogger(__name__)

# URLs das mídias padrão (importado do parser)
from app.services.message_parser import MEDIA_URLS


def process_media_tags(text: str) -> dict:
    """
    Processa tags de mídia no texto e retorna estrutura para frontend.

    Args:
        text: Texto contendo tags como [MEDIA:AUDIO_PADRAO]

    Returns:
        Dict com texto limpo e lista de mídias
    """
    return parse_message(text)


def format_for_chatwoot(text: str) -> dict:
    """
    Formata mensagem para envio ao Chatwoot.

    Args:
        text: Texto do LLM

    Returns:
        Dict no formato Chatwoot/n8n
    """
    return parse_for_chatwoot(text)


def process_media_tags(text: str) -> dict:
    """
    Processa tags de mídia no texto e retorna estrutura para frontend.

    Args:
        text: Texto contendo tags como [MEDIA:AUDIO_PADRAO]

    Returns:
        Dict com texto limpo e lista de mídias
    """
    if not text:
        return {"text": "", "media": []}

    result_text = text
    media_items = []

    # Processar cada tag
    for tag_name, url in MEDIA_URLS.items():
        tag = f"[MEDIA:{tag_name}]"

        if tag in result_text:
            # Remover tag do texto
            result_text = result_text.replace(tag, "")

            # Adicionar à lista de mídias
            media_type = "audio" if tag_name == "AUDIO_PADRAO" else "image"
            media_items.append({
                "type": media_type,
                "url": url,
                "name": tag_name,
                "tag": tag,
            })

    # Limpar texto (remover \\ extras, espaços duplos)
    result_text = result_text.replace("\\\\", "\n").strip()

    return {
        "text": result_text,
        "media": media_items,
    }


def extract_media_tags(text: str) -> list[dict]:
    """
    Extrai todas as tags de mídia do texto.

    Args:
        text: Texto contendo tags de mídia

    Returns:
        Lista de dicts com info das mídias encontradas
    """
    if not text:
        return []

    media_items = []

    for tag_name, url in MEDIA_URLS.items():
        tag = f"[MEDIA:{tag_name}]"

        if tag in text:
            media_type = "audio" if tag_name == "AUDIO_PADRAO" else "image"
            media_items.append({
                "tag": tag,
                "type": media_type,
                "url": url,
                "name": tag_name,
            })

    return media_items


def has_media_tag(text: str) -> bool:
    """
    Verifica se texto contém alguma tag de mídia.

    Args:
        text: Texto para verificar

    Returns:
        True se contém tag de mídia
    """
    if not text:
        return False

    for tag_name in MEDIA_URLS.keys():
        if f"[MEDIA:{tag_name}]" in text:
            return True

    return False


def get_media_url(tag_name: str) -> str | None:
    """
    Retorna URL de uma tag de mídia específica.

    Args:
        tag_name: Nome da tag (ex: "AUDIO_PADRAO")

    Returns:
        URL da mídia ou None
    """
    return MEDIA_URLS.get(tag_name)


def format_for_display(text: str) -> dict:
    """
    Formata texto para exibição no frontend.

    - Converte `\\` em quebras de linha
    - Processa tags de mídia
    - Retorna estrutura separada (texto + mídia)

    Args:
        text: Texto formatado do agente

    Returns:
        Dict com texto e mídia separados
    """
    if not text:
        return {"text": "", "media": []}

    # Processar tags de mídia
    result = process_media_tags(text)

    return result
