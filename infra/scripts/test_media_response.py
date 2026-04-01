"""Testar resposta do LLM com tags de mídia."""

import asyncio
from app.config.settings import get_settings
from app.agent.graph import run_agent
from app.state.lead_states import AgentState
from uuid import uuid4

settings = get_settings()


async def test_media_response():
    """Testar se LLM retorna tags de mídia."""
    print("=" * 60)
    print("TESTE DE RESPOSTA COM MÍDIA")
    print("=" * 60)
    print()

    state = AgentState(
        lead_id=uuid4(),
        session_id="test_session",
        incoming_message="500",
        incoming_message_type="text",
        current_state="NEW",
        metadata={
            "lead_name": "Fábio",
        },
    )

    print("Enviando mensagem: '500'")
    print(f"Estado: {state.current_state}")
    print()

    result = await run_agent(state)

    print("=" * 60)
    print("RESPOSTA DO LLM:")
    print("=" * 60)
    print()
    print(f"Texto: {result.reply_text}")
    print()
    print(f"Mídia no metadata: {result.metadata.get('media', [])}")
    print()
    print(f"Tags de mídia: {result.metadata.get('media_tags', [])}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_media_response())
