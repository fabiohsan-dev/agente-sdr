"""Teste de fluxo completo com estado."""

import asyncio
from app.config.settings import get_settings
from app.agent.graph import run_agent
from app.state.lead_states import AgentState
from app.repositories.leads_repository import LeadsRepository
from uuid import uuid4

settings = get_settings()


async def test_full_flow():
    """Testar fluxo completo com mudança de estado."""
    print("=" * 60)
    print("TESTE DE FLUXO COMPLETO COM ESTADO")
    print("=" * 60)
    print()

    # Criar lead de teste
    leads_repo = LeadsRepository()
    lead = await leads_repo.create(
        name="Lucas Teste",
        email="lucas@teste.com",
        source="test_flow",
    )
    
    print(f"Lead criado: {lead.id}")
    print(f"Estado inicial: {lead.current_state.value}")
    print()

    # ============================================
    # MENSAGEM 1: Gatilho inicial (500)
    # ============================================
    
    print("=" * 60)
    print("MENSAGEM 1: Enviando '500'")
    print("=" * 60)
    print()

    state1 = AgentState(
        lead_id=lead.id,
        session_id="test_session_1",
        incoming_message="500",
        incoming_message_type="text",
        current_state=lead.current_state,
    )

    result1 = await run_agent(state1)

    print(f"Resposta: {result1.reply_text[:100]}...")
    print(f"Estado antes: {result1.state_before.value if result1.state_before else 'None'}")
    print(f"Estado depois: {result1.next_state.value if result1.next_state else 'None'}")
    print()

    # Recarregar lead do banco
    lead_updated = await leads_repo.get_by_id(lead.id)
    print(f"Estado no banco: {lead_updated.current_state.value}")
    print()

    # ============================================
    # MENSAGEM 2: Lead responde
    # ============================================
    
    print("=" * 60)
    print("MENSAGEM 2: Lead responde 'Estou com dificuldade para captar clientes'")
    print("=" * 60)
    print()

    state2 = AgentState(
        lead_id=lead.id,
        session_id="test_session_1",
        incoming_message="Estou com dificuldade para captar clientes",
        incoming_message_type="text",
        current_state=lead_updated.current_state,  # Estado atualizado do banco
    )

    result2 = await run_agent(state2)

    print(f"Resposta: {result2.reply_text[:200]}...")
    print(f"Estado antes: {result2.state_before.value if result2.state_before else 'None'}")
    print(f"Estado depois: {result2.next_state.value if result2.next_state else 'None'}")
    print()

    # Recarregar lead do banco
    lead_updated2 = await leads_repo.get_by_id(lead.id)
    print(f"Estado no banco: {lead_updated2.current_state.value}")
    print()

    print("=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_full_flow())
