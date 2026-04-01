"""Verificar configurações."""

from app.config.settings import get_settings

s = get_settings()

print('CONFIGURACOES:')
print(f'  OPENAI_API_KEY: {s.openai_api_key[:10] + "..." if s.openai_api_key else "❌ Nao configurada"}')
print(f'  OPENAI_MODEL: {s.openai_model}')
print(f'  OPENAI_TEMPERATURE: {s.openai_temperature}')
print(f'  LLM_TIMEOUT: {s.llm_timeout}')
print(f'  SUPABASE_URL: {s.supabase_url[:30] + "..." if s.supabase_url else "❌ Nao configurada"}')
print()
print('SERVICOS:')
print(f'  Langfuse: {"✅" if s.langfuse_enabled else "⚪ Nao configurado"}')
print(f'  Cal.com: {"✅" if s.calcom_enabled else "⚪ Nao configurado"}')
print()
