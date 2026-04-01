"""Teste de conexão com OpenAI."""

import asyncio
import logging

from app.config.logging import setup_logging
from app.config.settings import get_settings

setup_logging()
logger = logging.getLogger(__name__)


async def test_openai_connection():
    """Testa conexão com OpenAI."""
    settings = get_settings()

    print("=" * 60)
    print("TESTE DE CONEXÃO OPENAI")
    print("=" * 60)
    print()

    # 1. Verificar chave
    print(f"1. API Key configurada: {'✅ Sim' if settings.openai_api_key else '❌ Não'}")
    print(f"   Key: {settings.openai_api_key[:10]}...")
    print()

    # 2. Verificar modelo
    print(f"2. Modelo configurado: {settings.openai_model}")
    print(f"   Modelos válidos: gpt-5.4-mini, gpt-4o-mini, gpt-4o, gpt-4-turbo")
    print()

    # 3. Testar conexão
    print("3. Testando conexão...")
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        # List modelos
        models = await client.models.list()
        model_ids = [m.id for m in models.data]

        print(f"   ✅ Conexão OK!")
        print(f"   Modelos disponíveis: {len(model_ids)}")

        # Verificar se modelo está na lista
        if settings.openai_model in model_ids:
            print(f"   ✅ Modelo '{settings.openai_model}' disponível")
        else:
            print(f"   ⚠️  Modelo '{settings.openai_model}' NÃO está na lista")
            print(f"   Modelos similares: {[m for m in model_ids if 'gpt' in m][:5]}")

        # 4. Testar geração simples
        print()
        print("4. Testando geração de mensagem...")
        from langchain_openai import ChatOpenAI

        # Passar API Key explicitamente
        llm = ChatOpenAI(
            api_key=settings.openai_api_key,  # ✅ Passar explicitamente
            model=settings.openai_model,
            temperature=0.7,
        )

        response = await llm.ainvoke("Diga apenas 'Olá, teste OK'")
        print(f"   ✅ Geração OK!")
        print(f"   Resposta: {response.content}")

    except Exception as e:
        print(f"   ❌ ERRO: {type(e).__name__}: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_openai_connection())
