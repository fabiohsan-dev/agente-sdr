"""Utilitários de ID."""

import uuid


def generate_uuid() -> str:
    """
    Gera UUID v4 como string.

    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def generate_session_id() -> str:
    """
    Gera ID de sessão.

    Returns:
        Session ID string
    """
    return f"sess_{uuid.uuid4().hex[:16]}"


def generate_id(prefix: str = "") -> str:
    """
    Gera ID com prefixo opcional.

    Args:
        prefix: Prefixo para o ID

    Returns:
        ID string
    """
    id_part = uuid.uuid4().hex[:12]
    if prefix:
        return f"{prefix}_{id_part}"
    return id_part


def is_valid_uuid(value: str) -> bool:
    """
    Verifica se string é UUID válido.

    Args:
        value: String para validar

    Returns:
        True se for UUID válido
    """
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False
