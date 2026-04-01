"""Debug de persistência de estado."""

import asyncio
from app.config.settings import get_settings
from app.agent.graph import run_agent
from app.state.lead_states import AgentState
from app.repositories.leads_repository import LeadsRepository
from app.repositories.conversations_repository import ConversationsRepository

settings = get_settings()


async def debug_persist():
    """Debug: verificar se estado persiste no banco."""
    
    print("=" * 80)
    print("DEBUG DE PERSISTÊNCIA DE ESTADO")
    print("=" * 80)
    print()
    
    leads_repo = LeadsRepository()
    conversations_repo = ConversationsRepository()
    
    # Criar lead
    print("[1] Criando lead...")
    lead = await leads_repo.create(
        name="Debug Lead",
        email=f"debug_{id}@teste.com",
        source="debug_persist",
    )
    session_id = f"debug_session_{id}"
    
    print(f"    Lead ID: {lead.id}")
    print(f"    Session ID: {session_id}")
    print(f"    Estado: {lead.current_state.value}")
    print()
    
    # Mensagem 1: 500
    print("[2] Enviando '500'...")
    state1 = AgentState(
        lead_id=None,
        session_id=session_id,
        incoming_message="500",
        incoming_message_type="text",
    )
    
    result1 = await run_agent(state1)
    
    # Verificar no banco
    lead_db1 = await leads_repo.get_by_id(lead.id)
    convs1 = conversations_repo.client.table("conversations").select("*").eq("session_id", session_id).execute()
    
    print(f"    Estado no agente: {result1.next_state.value}")
    print(f"    Estado no banco: {lead_db1.current_state.value}")
    print(f"    Conversations encontradas: {len(convs1.data)}")
    if convs1.data:
        for c in convs1.data:
            print(f"      - {c['id']}: session_id={c['session_id']}, lead_id={c['lead_id']}")
    print()
    
    # Mensagem 2: Resposta
    print("[3] Enviando resposta...")
    state2 = AgentState(
        lead_id=None,
        session_id=session_id,
        incoming_message="Estou com dificuldade",
        incoming_message_type="text",
    )
    
    result2 = await run_agent(state2)
    
    # Verificar no banco
    lead_db2 = await leads_repo.get_by_id(lead.id)
    convs2 = conversations_repo.client.table("conversations").select("*").eq("session_id", session_id).execute()
    
    print(f"    Estado no agente: {result2.next_state.value}")
    print(f"    Estado no banco: {lead_db2.current_state.value}")
    print(f"    Conversations encontradas: {len(convs2.data)}")
    if convs2.data:
        for c in convs2.data:
            print(f"      - {c['id']}: session_id={c['session_id']}, lead_id={c['lead_id']}")
    print()
    
    print("=" * 80)
    print("CONCLUSÃO:")
    if lead_db1.current_state.value != "NEW":
        print("✅ Estado PERSISTIU na Etapa 1")
    else:
        print("❌ Estado NÃO persistiu na Etapa 1")
    
    if lead_db2.current_state.value != "NEW":
        print("✅ Estado PERSISTIU na Etapa 2")
    else:
        print("❌ Estado NÃO persistiu na Etapa 2")
    
    if len(convs2.data) > 1:
        print(f"⚠️  MÚLTIPLAS conversations criadas ({len(convs2.data)})")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(debug_persist())
