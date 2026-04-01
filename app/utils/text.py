"""Utilitários de texto."""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Normaliza texto (remove acentos, lowercase).

    Args:
        text: Texto para normalizar

    Returns:
        Texto normalizado
    """
    # Normalizar unicode (remove acentos)
    normalized = unicodedata.normalize("NFKD", text)
    # Remover caracteres não-ASCII
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    # Lowercase
    return ascii_text.lower()


def clean_whitespace(text: str) -> str:
    """
    Limpa espaços em branco extras.

    Args:
        text: Texto para limpar

    Returns:
        Texto limpo
    """
    # Remover espaços extras
    text = re.sub(r"\s+", " ", text)
    # Trim
    return text.strip()


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Trunca texto se for muito longo.

    Args:
        text: Texto para truncar
        max_length: Comprimento máximo
        suffix: Sufixo para adicionar

    Returns:
        Texto truncado
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def extract_email(text: str) -> str | None:
    """
    Extrai email de um texto.

    Args:
        text: Texto para buscar email

    Returns:
        Email encontrado ou None
    """
    pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    """
    Extrai número de telefone de um texto.

    Args:
        text: Texto para buscar telefone

    Returns:
        Telefone encontrado ou None
    """
    # Padrão para telefone brasileiro
    pattern = r"(\(?\d{2}\)?\s?)?(\d{4,5}\s?\d{4})"
    match = re.search(pattern, text)
    if match:
        return match.group(0).replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    return None


def is_valid_email(email: str) -> bool:
    """
    Verifica se email é válido.

    Args:
        email: Email para validar

    Returns:
        True se válido
    """
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def is_valid_phone(phone: str) -> bool:
    """
    Verifica se telefone é válido (BR).

    Args:
        phone: Telefone para validar

    Returns:
        True se válido
    """
    # Remover caracteres não-numéricos
    digits = re.sub(r"\D", "", phone)

    # Verificar se tem 10 ou 11 dígitos (com DDD)
    if len(digits) not in [10, 11]:
        return False

    # Verificar se começa com 0 ou 9 (celular)
    if len(digits) == 11 and digits[2] not in ["9"]:
        return False

    return True


def format_phone(phone: str) -> str:
    """
    Formata telefone para padrão brasileiro.

    Args:
        phone: Telefone para formatar

    Returns:
        Telefone formatado
    """
    digits = re.sub(r"\D", "", phone)

    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    elif len(digits) == 11:
        return f"({digits[:2]}) {digits[2]} {digits[3:7]}-{digits[7:]}"

    return phone


def similar(a: str, b: str) -> float:
    """
    Calcula similaridade entre duas strings (0-1).

    Args:
        a: Primeira string
        b: Segunda string

    Returns:
        Score de similaridade (0-1)
    """
    # Implementação simples de Levenshtein ratio
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0

    a = normalize_text(a)
    b = normalize_text(b)

    if a == b:
        return 1.0

    # Calcular distância de Levenshtein
    matrix = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]

    for i in range(len(a) + 1):
        matrix[i][0] = i
    for j in range(len(b) + 1):
        matrix[0][j] = j

    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                matrix[i][j] = matrix[i - 1][j - 1]
            else:
                matrix[i][j] = min(
                    matrix[i - 1][j] + 1,
                    matrix[i][j - 1] + 1,
                    matrix[i - 1][j - 1] + 1,
                )

    distance = matrix[len(a)][len(b)]
    max_len = max(len(a), len(b))
    return 1 - (distance / max_len)
