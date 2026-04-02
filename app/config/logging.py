"""Configuração de logging."""

import logging
import sys

from app.config.settings import get_settings

settings = get_settings()


def setup_logging() -> None:
    """Configura o logging da aplicação."""
    log_format = logging.Formatter(
        fmt=("%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler para stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(log_format)

    # Logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    root_logger.addHandler(handler)

    # Silenciar logs muito verbosos de bibliotecas
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)

    # Ajustar para DEBUG em desenvolvimento
    if settings.is_development:
        logging.getLogger("app").setLevel(logging.DEBUG)


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger com o nome especificado."""
    return logging.getLogger(name)
