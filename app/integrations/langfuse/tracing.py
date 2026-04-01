"""Langfuse tracing para observabilidade.

Compatível com Langfuse SDK v4.x (OpenTelemetry-native).
Usa @observe() decorator e start_as_current_observation().

Configuração fail-safe: se não tiver chaves, não faz nada.
"""

import logging
import os
from contextlib import contextmanager
from typing import Any, Generator
from uuid import UUID

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LangfuseTracing:
    """Gerencia tracing com Langfuse v4 (fail-safe).

    Langfuse v4 usa OpenTelemetry internamente.
    A API pública usa:
    - start_as_current_observation() para spans/traces
    - @observe() decorator para instrumentação automática
    - propagate_attributes() para user_id, session_id
    """

    def __init__(self):
        self._client = None
        self._initialized = False

    def initialize(self) -> None:
        """Inicializa Langfuse v4 via env vars (OpenTelemetry-native)."""

        # Verificar se chaves estão configuradas
        if not settings.langfuse_public_key or not settings.langfuse_secret_key:
            logger.info("⚪ Langfuse: chaves não configuradas, tracing desativado")
            return

        # Verificar se chaves não são vazias
        if settings.langfuse_public_key.strip() == "" or settings.langfuse_secret_key.strip() == "":
            logger.info("⚪ Langfuse: chaves vazias, tracing desativado")
            return

        try:
            # Langfuse v4 lê configurações de env vars automaticamente,
            # mas definimos explicitamente para garantir
            os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
            os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
            os.environ["LANGFUSE_HOST"] = settings.langfuse_host

            from langfuse import Langfuse
            self._client = Langfuse()
            self._initialized = True
            logger.info("✅ Langfuse v4: tracing ativado com sucesso")

        except Exception as e:
            logger.warning(f"⚠️  Langfuse: erro ao inicializar ({e}), tracing desativado")
            self._client = None
            self._initialized = False

    def is_available(self) -> bool:
        """Verifica se Langfuse está disponível."""
        return self._initialized and self._client is not None

    def trace(
        self,
        name: str,
        user_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Cria um novo trace (fail-safe, compatível v4).

        No Langfuse v4, traces são criados implicitamente via
        start_as_current_observation(). Este método retorna um
        objeto de compatibilidade que pode ser usado downstream.
        """
        if not self.is_available():
            return None

        try:
            # Langfuse v4: usar start_as_current_observation como trace root
            obs = self._client.start_as_current_observation(
                name=name,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata,
            )
            return obs
        except Exception as e:
            logger.warning(f"Langfuse trace error: {e}")
            return None

    def span(self, parent, name: str, metadata: dict[str, Any] | None = None):
        """Cria um span (fail-safe, compatível v4)."""
        if not self.is_available() or parent is None:
            return None

        try:
            obs = self._client.start_as_current_observation(
                name=name,
                metadata=metadata,
            )
            return obs
        except Exception as e:
            logger.warning(f"Langfuse span error: {e}")
            return None

    def event(self, parent, name: str, metadata: dict[str, Any] | None = None):
        """Registra um evento (fail-safe, compatível v4)."""
        if not self.is_available() or parent is None:
            return None

        try:
            self._client.create_event(
                name=name,
                metadata=metadata,
            )
        except Exception as e:
            logger.warning(f"Langfuse event error: {e}")
        return None

    def generation(
        self,
        parent,
        name: str,
        prompt: str | None = None,
        completion: str | None = None,
        model: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Cria um generation para LLM calls (fail-safe, compatível v4)."""
        if not self.is_available() or parent is None:
            return None

        try:
            obs = self._client.start_as_current_observation(
                name=name,
                observation_type="generation",
                model=model,
                input=prompt,
                output=completion,
                metadata=metadata,
            )
            return obs
        except Exception as e:
            logger.warning(f"Langfuse generation error: {e}")
            return None

    @contextmanager
    def trace_context(
        self,
        name: str,
        lead_id: UUID | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Generator:
        """Context manager para trace completo (fail-safe, v4)."""
        obs = None

        try:
            if self.is_available():
                obs = self.trace(
                    name=name,
                    user_id=str(lead_id) if lead_id else None,
                    session_id=session_id,
                    metadata=metadata,
                )

            yield obs, obs  # (trace, span) - ambos são a mesma observation no v4

        except Exception as e:
            if obs:
                try:
                    obs.__exit__(type(e), e, e.__traceback__)
                except Exception:
                    pass
            raise

        finally:
            if obs:
                try:
                    obs.__exit__(None, None, None)
                except Exception:
                    pass

    def flush(self) -> None:
        """Flush de eventos para o Langfuse (fail-safe)."""
        if self.is_available() and self._client:
            try:
                self._client.flush()
            except Exception as e:
                logger.debug(f"Langfuse flush error: {e}")

    def shutdown(self) -> None:
        """Desliga cliente Langfuse (fail-safe)."""
        if self.is_available() and self._client:
            try:
                self._client.shutdown()
            except Exception as e:
                logger.debug(f"Langfuse shutdown error: {e}")


# Singleton global
_langfuse_instance: LangfuseTracing | None = None


def get_langfuse() -> LangfuseTracing:
    """Retorna instância singleton do Langfuse."""
    global _langfuse_instance
    if _langfuse_instance is None:
        _langfuse_instance = LangfuseTracing()
        _langfuse_instance.initialize()
    return _langfuse_instance


def init_langfuse() -> None:
    """Inicializa Langfuse explicitamente (chamar no startup da app)."""
    get_langfuse()


def shutdown_langfuse() -> None:
    """Desliga Langfuse explicitamente (chamar no shutdown da app)."""
    global _langfuse_instance
    if _langfuse_instance:
        _langfuse_instance.shutdown()
        _langfuse_instance = None
