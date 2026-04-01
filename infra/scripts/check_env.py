"""Verificar .env."""

from pathlib import Path
from dotenv import load_dotenv
import os

env_path = Path(__file__).parent.parent.parent / ".env"

print(f"Verificando: {env_path}")
print(f"Existe: {env_path.exists()}")
print()

# Carregar .env
load_dotenv(dotenv_path=env_path)

# Verificar variáveis importantes
print("Variáveis carregadas:")
print(f"  OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', '❌ Não encontrada')[:10] + '...' if os.getenv('OPENAI_API_KEY') else '❌ Não encontrada'}")
print(f"  OPENAI_MODEL: {os.getenv('OPENAI_MODEL', '❌ Não encontrada')}")
print(f"  SUPABASE_URL: {os.getenv('SUPABASE_URL', '❌ Não encontrada')}")
print(f"  SUPABASE_SERVICE_ROLE_KEY: {os.getenv('SUPABASE_SERVICE_ROLE_KEY', '❌ Não encontrada')[:10] + '...' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else '❌ Não encontrada'}")
print()

# Verificar todas as variáveis
print("Todas as variáveis do .env:")
for key in sorted(os.environ.keys()):
    if key.startswith(('OPENAI', 'SUPABASE', 'CALCOM', 'LANGFUSE', 'APP_', 'API_', 'PLAYGROUND_')):
        value = os.getenv(key)
        if value and len(value) > 20:
            value = value[:10] + '...'
        print(f"  {key}: {value}")
