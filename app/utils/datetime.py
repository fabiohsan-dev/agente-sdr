"""Utilitários de datetime."""

from datetime import UTC, datetime

import pytz

from app.config.settings import get_settings

settings = get_settings()


def get_timezone() -> pytz.timezone:
    """Retorna timezone configurada."""
    return pytz.timezone(settings.timezone)


def now_utc() -> datetime:
    """Retorna agora em UTC."""
    return datetime.now(UTC)


def now_local() -> datetime:
    """Retorna agora no timezone local."""
    tz = get_timezone()
    return now_utc().astimezone(tz)


def to_utc(dt: datetime) -> datetime:
    """Converte datetime para UTC."""
    if dt.tzinfo is None:
        dt = get_timezone().localize(dt)
    return dt.astimezone(UTC)


def to_local(dt: datetime) -> datetime:
    """Converte datetime para timezone local."""
    if dt.tzinfo is None:
        dt = UTC.localize(dt)
    tz = get_timezone()
    return dt.astimezone(tz)


def format_datetime(dt: datetime, format_str: str = "%d/%m/%Y %H:%M") -> str:
    """Formata datetime para string."""
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%d/%m/%Y %H:%M") -> datetime:
    """Parse de string para datetime."""
    return datetime.strptime(date_str, format_str)


def is_business_hours(dt: datetime | None = None) -> bool:
    """
    Verifica se está em horário comercial.

    Args:
        dt: datetime para verificar (usa now se None)

    Returns:
        True se estiver em horário comercial
    """
    if dt is None:
        dt = now_local()
    else:
        dt = to_local(dt)

    # Segunda a sexta, 9h às 18h
    if dt.weekday() >= 5:  # Sábado ou domingo
        return False

    return 9 <= dt.hour < 18


def business_hours_add(
    dt: datetime,
    hours: int,
) -> datetime:
    """
    Adiciona horas considerando apenas horário comercial.

    Args:
        dt: datetime inicial
        hours: horas para adicionar

    Returns:
        datetime resultante
    """
    result = to_local(dt)
    remaining = hours

    while remaining > 0:
        # Se não está em horário comercial, pular para próximo dia útil às 9h
        if not is_business_hours(result):
            if result.weekday() >= 5:
                # Fim de semana, pular para segunda
                days_to_add = 7 - result.weekday()
                result = result.replace(
                    year=result.year,
                    month=result.month,
                    day=result.day + days_to_add,
                    hour=9,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
            elif result.hour >= 18:
                # Depois das 18h, pular para próximo dia às 9h
                result = result.replace(
                    year=result.year,
                    month=result.month,
                    day=result.day + 1,
                    hour=9,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
            else:
                # Antes das 9h, pular para 9h
                result = result.replace(hour=9, minute=0, second=0, microsecond=0)
            continue

        # Calcular horas até o fim do dia comercial
        hours_until_end = 18 - result.hour
        hours_to_add = min(remaining, hours_until_end)

        result = result.replace(hour=result.hour + hours_to_add)
        remaining -= hours_to_add

        # Se ainda tem horas restantes e chegou às 18h, pular para próximo dia
        if remaining > 0 and result.hour >= 18:
            result = result.replace(
                year=result.year,
                month=result.month,
                day=result.day + 1,
                hour=9,
                minute=0,
                second=0,
                microsecond=0,
            )

    return result
