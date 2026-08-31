"""Settings da aplicação com pydantic-settings."""

import secrets
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================
    # OPENAI / LLM (OBRIGATÓRIO)
    # ============================================
    openai_api_key: str = Field(
        ...,
        description="API Key da OpenAI (obrigatória)",
        examples=["sk-..."],
    )
    openai_model: str = Field(
        default="gpt-5.4-mini",
        description="Modelo para o agente",
        examples=["gpt-5.4-mini", "gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
    )
    openai_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperatura para geração (0.0 a 1.0)",
    )

    # ============================================
    # SUPABASE (OBRIGATÓRIO)
    # ============================================
    supabase_url: str = Field(
        ...,
        description="URL do projeto Supabase",
        examples=["https://xxxxx.supabase.co"],
    )
    supabase_service_role_key: str = Field(
        ...,
        description="Service Role Key do Supabase",
    )

    # ============================================
    # CAL.COM (OPCIONAL)
    # ============================================
    calcom_api_key: str = Field(
        default="",
        description="API Key do Cal.com (opcional)",
    )
    calcom_base_url: str = Field(
        default="https://api.cal.com/v2",
        description="URL base da API do Cal.com",
    )
    calcom_event_type_id: int | None = Field(
        default=None,
        description="ID do event type no Cal.com",
    )

    # ============================================
    # LANGFUSE (OPCIONAL)
    # ============================================
    langfuse_public_key: str = Field(
        default="",
        description="Public Key do Langfuse (opcional)",
    )
    langfuse_secret_key: str = Field(
        default="",
        description="Secret Key do Langfuse (opcional)",
    )
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com",
        description="Host do Langfuse",
    )

    # ============================================
    # SEGURANÇA INTERNA (AUTO-GERADO)
    # ============================================
    app_secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key para sessões e tokens internos",
    )
    session_secret: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret para sessões do playground",
    )
    webhook_secret: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret para webhooks futuros",
    )
    encryption_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Chave de encriptação de dados sensíveis",
    )

    # ============================================
    # CHATWOOT (OPCIONAL)
    # ============================================
    chatwoot_base_url: str = Field(
        default="",
        description="URL base do Chatwoot (ex: https://app.chatwoot.com)",
    )
    chatwoot_api_token: str = Field(
        default="",
        description="API Access Token do Chatwoot (Super Admin ou Agent Bot)",
    )
    chatwoot_account_id: int = Field(
        default=0,
        description="Account ID do Chatwoot",
    )
    chatwoot_inbox_id: int = Field(
        default=0,
        description="Inbox ID do Chatwoot (canal WhatsApp/Instagram)",
    )
    chatwoot_webhook_secret: str = Field(
        default="",
        description="Secret para validar assinatura HMAC dos webhooks",
    )

    # ============================================
    # CDN / STORAGE / MATERIAIS (OPCIONAL)
    # ============================================
    cdn_base_url: str = Field(
        default="",
        description="URL base da CDN para arquivos de mídia",
    )
    materials_drive_url: str = Field(
        default="https://drive.google.com/drive/folders/seu-link-de-cases",
        description="Link do Google Drive com cases de sucesso",
    )
    case_study_url: str = Field(
        default="https://seusite.com/cases",
        description="Link da página ou estudo de caso",
    )
    audio_padrao_url: str = Field(
        default="",
        description="URL do áudio padrão do sistema",
    )
    case_generico_url: str = Field(
        default="",
        description="URL da imagem de case genérico",
    )
    follow_up_image_url: str = Field(
        default="",
        description="URL da imagem de follow-up",
    )

    # ============================================
    # APLICAÇÃO
    # ============================================
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Ambiente da aplicação",
    )
    timezone: str = Field(
        default="America/Sao_Paulo",
        description="Timezone da aplicação",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Nível de log",
    )

    # ============================================
    # API SERVER
    # ============================================
    api_host: str = Field(
        default="127.0.0.1",
        description="Host da API",
    )
    api_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Porta da API",
    )

    # ============================================
    # PLAYGROUND SERVER
    # ============================================
    playground_host: str = Field(
        default="127.0.0.1",
        description="Host do Playground",
    )
    playground_port: int = Field(
        default=8001,
        ge=1,
        le=65535,
        description="Porta do Playground",
    )

    # ============================================
    # LIMITES E TIMEOUTS
    # ============================================
    http_timeout: int = Field(
        default=30,
        ge=1,
        description="Timeout para chamadas HTTP (segundos)",
    )
    llm_timeout: int = Field(
        default=60,
        ge=1,
        description="Timeout para LLM (segundos)",
    )
    max_history_messages: int = Field(
        default=20,
        ge=1,
        description="Máximo de mensagens no histórico",
    )

    # ============================================
    # REDIS (OPCIONAL)
    # ============================================
    redis_url: str = Field(
        default="",
        description="URL do Redis (opcional)",
    )
    redis_ttl: int = Field(
        default=3600,
        ge=0,
        description="TTL do Redis (segundos)",
    )

    # ============================================
    # RATE LIMITING (OPCIONAL)
    # ============================================
    rate_limit_requests: int = Field(
        default=60,
        ge=1,
        description="Requests por minuto",
    )
    rate_limit_window: int = Field(
        default=60,
        ge=1,
        description="Janela de rate limiting (segundos)",
    )

    # ============================================
    # VALIDATORS
    # ============================================

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_api_key(cls, v: str) -> str:
        """Valida se OpenAI API Key está configurada."""
        if not v or v.strip() == "":
            raise ValueError(
                "OPENAI_API_KEY é obrigatória. Obtenha em: https://platform.openai.com/api-keys"
            )
        return v.strip()

    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url(cls, v: str) -> str:
        """Valida se Supabase URL está configurada."""
        if not v or v.strip() == "":
            raise ValueError("SUPABASE_URL é obrigatória. Obtenha em: https://app.supabase.com")
        return v.strip()

    @field_validator("supabase_service_role_key")
    @classmethod
    def validate_supabase_service_role_key(cls, v: str) -> str:
        """Valida se Supabase Service Role Key está configurada."""
        if not v or v.strip() == "":
            raise ValueError(
                "SUPABASE_SERVICE_ROLE_KEY é obrigatória. "
                "Obtenha em: https://app.supabase.com/project/_/settings/api"
            )
        return v.strip()

    # ============================================
    # PROPERTIES
    # ============================================

    @property
    def is_development(self) -> bool:
        """Retorna True se estiver em desenvolvimento."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Retorna True se estiver em produção."""
        return self.app_env == "production"

    @property
    def langfuse_enabled(self) -> bool:
        """Retorna True se Langfuse estiver configurado com chaves válidas."""
        return bool(
            self.langfuse_public_key
            and self.langfuse_secret_key
            and self.langfuse_public_key.strip() != ""
            and self.langfuse_secret_key.strip() != ""
        )

    @property
    def calcom_enabled(self) -> bool:
        """Retorna True se Cal.com estiver configurado."""
        return bool(
            self.calcom_api_key
            and self.calcom_event_type_id
            and self.calcom_api_key != ""
            and self.calcom_event_type_id is not None
        )

    @property
    def chatwoot_enabled(self) -> bool:
        """Retorna True se Chatwoot estiver configurado."""
        return bool(
            self.chatwoot_base_url and self.chatwoot_api_token and self.chatwoot_account_id > 0
        )

    @property
    def redis_enabled(self) -> bool:
        """Retorna True se Redis estiver configurado."""
        return bool(self.redis_url and self.redis_url != "")

    # ============================================
    # MÉTODOS DE UTILIDADE
    # ============================================

    def validate_external_keys(self) -> dict:
        """
        Valida chaves externas e retorna status de configuração.

        Returns:
            Dict com status de cada serviço externo
        """
        return {
            "openai": bool(self.openai_api_key),
            "supabase": bool(self.supabase_url and self.supabase_service_role_key),
            "calcom": self.calcom_enabled,
            "langfuse": self.langfuse_enabled,
            "chatwoot": self.chatwoot_enabled,
            "redis": self.redis_enabled,
        }

    def get_required_keys(self) -> list[str]:
        """Retorna lista de chaves obrigatórias não configuradas."""
        missing = []

        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")

        if not self.supabase_url:
            missing.append("SUPABASE_URL")

        if not self.supabase_service_role_key:
            missing.append("SUPABASE_SERVICE_ROLE_KEY")

        return missing

    def get_optional_keys(self) -> list[str]:
        """Retorna lista de chaves opcionais não configuradas."""
        optional = []

        if not self.calcom_enabled:
            optional.append("CALCOM_API_KEY (opcional)")

        if not self.langfuse_enabled:
            optional.append("LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY (opcionais)")

        return optional


@lru_cache
def get_settings() -> Settings:
    """
    Retorna instância cacheada das settings.

    Raises:
        ValidationError: Se alguma configuração obrigatória estiver faltando
    """
    return Settings()


def check_settings() -> None:
    """
    Verifica configurações e imprime status.

    Útil para debug e validação inicial.
    """
    try:
        settings = get_settings()

        print("=" * 60)
        print("STATUS DAS CONFIGURAÇÕES")
        print("=" * 60)

        # Validar externas
        status = settings.validate_external_keys()

        print("\nSERVIÇOS EXTERNOS:")
        print(f"  ✅ OpenAI: {'Configurado' if status['openai'] else '❌ Não configurado'}")
        print(f"  ✅ Supabase: {'Configurado' if status['supabase'] else '❌ Não configurado'}")
        print(
            f"  {'✅' if status['calcom'] else '⚪'} Cal.com: {'Configurado' if status['calcom'] else 'Não configurado (opcional)'}"
        )
        print(
            f"  {'✅' if status['langfuse'] else '⚪'} Langfuse: {'Configurado' if status['langfuse'] else 'Não configurado (opcional)'}"
        )

        # Verificar se há chaves faltando
        missing = settings.get_required_keys()
        if missing:
            print("\n⚠️  CHAVES OBRIGATÓRIAS FALTANDO:")
            for key in missing:
                print(f"    - {key}")
            print("\nExecute: python infra/scripts/generate_secrets.py")
            print("Ou configure manualmente no arquivo .env")

        print("\n" + "=" * 60)

    except Exception as e:
        print(f"❌ Erro ao validar configurações: {e}")
        print("\nVerifique se o arquivo .env está configurado corretamente.")
        print("Copie .env.example para .env e preencha as chaves obrigatórias.")
