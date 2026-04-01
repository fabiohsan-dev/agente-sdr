"""Validação CRÍTICA de estado do lead - PASSO A PASSO."""

import asyncio
import time
from app.config.settings import get_settings
from app.agent.graph import run_agent
from app.state.lead_states import AgentState
from app.repositories.leads_repository import LeadsRepository
from app.repositories.conversations_repository import ConversationsRepository
from uuid import uuid4

settings = get_settings()


async def validate_state_persistence():
    """
    Validação CRÍTICA: Estado do lead deve ser mantido entre mensagens.
    
    FLUXO DE TESTE:
    1. Cria lead (NEW)
    2. Envia '500' → Deve ir para QUALIFYING
    3. Envia resposta → Deve ir para WAITING_* (NÃO pode repetir Etapa 1)
    4. Envia confirmação → Deve avançar (NÃO pode voltar)
    """
    
    print("=" * 80)
    print("VALIDAÇÃO CRÍTICA DE ESTADO - PASSO A PASSO")
    print("=" * 80)
    print()
    
    leads_repo = LeadsRepository()
    conversations_repo = ConversationsRepository()
    
    # ============================================
    # SETUP: Criar lead de teste
    # ============================================
    
    print("[SETUP] Criando lead de teste...")
    test_lead = await leads_repo.create(
        name="Teste Validação",
        email=f"teste_{int(time.time())}@validacao.com",
        source="test_state_validation",
    )
    test_session = f"test_session_{int(time.time())}"
    
    print(f"  Lead ID: {test_lead.id}")
    print(f"  Session ID: {test_session}")
    print(f"  Estado inicial: {test_lead.current_state.value}")
    print()
    
    # ============================================
    # PASSO 1: Enviar gatilho inicial (500)
    # ============================================
    
    print("=" * 80)
    print("PASSO 1: Enviando gatilho inicial '500'")
    print("=" * 80)
    
    state1 = AgentState(
        lead_id=test_lead.id,
        session_id=test_session,
        incoming_message="500",
        incoming_message_type="text",
    )
    
    result1 = await run_agent(state1)
    
    # Recarregar do banco
    lead1_db = await leads_repo.get_by_id(test_lead.id)
    conv1_db = await conversations_repo.get_by_session_id(test_session, test_lead.id)
    
    print(f"  Resposta: {result1.reply_text[:80]}...")
    print(f"  Estado antes: {result1.state_before.value if result1.state_before else 'None'}")
    print(f"  Estado depois: {result1.next_state.value if result1.next_state else 'None'}")
    print(f"  Estado no banco: {lead1_db.current_state.value}")
    print(f"  Conversation ID: {conv1_db.id if conv1_db else 'None'}")
    
    # VALIDAÇÃO 1
    validacao_1_pass = (
        result1.next_state.value == "QUALIFYING" and
        lead1_db.current_state.value == "QUALIFYING" and
        conv1_db is not None
    )
    print(f"  ✅ VALIDAÇÃO 1: {'PASSOU' if validacao_1_pass else 'FALHOU'}")
    print()
    
    if not validacao_1_pass:
        print("❌ ERRO CRÍTICO: Estado não foi atualizado corretamente no PASSO 1!")
        return False
    
    # ============================================
    # PASSO 2: Lead responde à pergunta do áudio
    # ============================================
    
    print("=" * 80)
    print("PASSO 2: Lead responde 'Estou com dificuldade para captar clientes'")
    print("=" * 80)
    
    state2 = AgentState(
        lead_id=test_lead.id,
        session_id=test_session,
        incoming_message="Estou com dificuldade para captar clientes",
        incoming_message_type="text",
    )
    
    result2 = await run_agent(state2)
    
    # Recarregar do banco
    lead2_db = await leads_repo.get_by_id(test_lead.id)
    
    print(f"  Resposta: {result2.reply_text[:100]}...")
    print(f"  Estado antes: {result2.state_before.value if result2.state_before else 'None'}")
    print(f"  Estado depois: {result2.next_state.value if result2.next_state else 'None'}")
    print(f"  Estado no banco: {lead2_db.current_state.value}")
    
    # VALIDAÇÃO 2 - CRÍTICA!
    validacao_2_pass = (
        result2.state_before.value == "QUALIFYING" and  # Deve vir de QUALIFYING
        result2.next_state.value != "QUALIFYING" and    # Deve ter mudado estado
        result2.next_state.value != "NEW" and           # NÃO pode voltar para NEW
        lead2_db.current_state.value != "NEW"           # NÃO pode voltar para NEW
    )
    
    print(f"  ✅ VALIDAÇÃO 2: {'PASSOU' if validacao_2_pass else 'FALHOU'}")
    
    if not validacao_2_pass:
        print("❌ ERRO CRÍTICO: Estado voltou para NEW ou não avançou!")
        print(f"     Estado antes: {result2.state_before.value}")
        print(f"     Estado depois: {result2.next_state.value}")
        return False
    
    # Verificar se NÃO repetiu Etapa 1
    repetiu_etapa_1 = "Faaaaala" in result2.reply_text and "AUDIO_PADRAO" in result2.reply_text
    print(f"  ✅ NÃO repetiu Etapa 1: {'SIM' if not repetiu_etapa_1 else 'NÃO - ERRO CRÍTICO!'}")
    
    if repetiu_etapa_1:
        print("❌ ERRO CRÍTICO: Agente repetiu Etapa 1!")
        return False
    
    print()
    
    # ============================================
    # PASSO 3: Lead confirma prioridade
    # ============================================
    
    print("=" * 80)
    print("PASSO 3: Lead confirma 'Sim, é prioridade'")
    print("=" * 80)
    
    state3 = AgentState(
        lead_id=test_lead.id,
        session_id=test_session,
        incoming_message="Sim, é prioridade",
        incoming_message_type="text",
    )
    
    result3 = await run_agent(state3)
    
    # Recarregar do banco
    lead3_db = await leads_repo.get_by_id(test_lead.id)
    
    print(f"  Resposta: {result3.reply_text[:100]}...")
    print(f"  Estado antes: {result3.state_before.value if result3.state_before else 'None'}")
    print(f"  Estado depois: {result3.next_state.value if result3.next_state else 'None'}")
    print(f"  Estado no banco: {lead3_db.current_state.value}")
    
    # VALIDAÇÃO 3
    validacao_3_pass = (
        result3.state_before.value == lead2_db.current_state.value and  # Deve manter estado anterior
        result3.next_state.value != "NEW" and                           # NÃO pode voltar
        result3.next_state.value != "QUALIFYING"                        # NÃO pode voltar
    )
    print(f"  ✅ VALIDAÇÃO 3: {'PASSOU' if validacao_3_pass else 'FALHOU'}")
    
    if not validacao_3_pass:
        print("❌ ERRO CRÍTICO: Estado voltou para trás!")
        return False
    
    print()
    
    # ============================================
    # RESUMO FINAL
    # ============================================
    
    print("=" * 80)
    print("RESUMO FINAL")
    print("=" * 80)
    print()
    print(f"Lead ID: {test_lead.id}")
    print(f"Session ID: {test_session}")
    print()
    print("Fluxo de estados:")
    print(f"  NEW → {result1.next_state.value} → {result2.next_state.value} → {result3.next_state.value}")
    print()
    
    # Verificar se sempre foi para frente
    estados = [
        "NEW",
        result1.next_state.value,
        result2.next_state.value,
        result3.next_state.value,
    ]
    
    # Mapear ordem dos estados
    ordem_estados = {
        "NEW": 0,
        "QUALIFYING": 1,
        "WAITING_PRIORITY_CONFIRMATION": 2,
        "WAITING_FIT_CONFIRMATION": 3,
        "WAITING_TIME": 4,
        "WAITING_EMAIL": 5,
        "BOOKING_IN_PROGRESS": 6,
        "SCHEDULED": 7,
        "POST_BOOKING_PENDING_MATERIALS": 8,
        "POST_BOOKING_PENDING_CHECKLIST": 9,
        "NO_MONEY": -1,
        "CLOSED": -1,
        "PAUSED_BY_HUMAN": -1,
    }
    
    sempre_avancou = True
    for i in range(1, len(estados)):
        if ordem_estados.get(estados[i], 0) < ordem_estados.get(estados[i-1], 0):
            sempre_avancou = False
            print(f"  ❌ Estado voltou de {estados[i-1]} para {estados[i]}")
    
    if sempre_avancou:
        print("  ✅ Estados sempre avançaram (nunca voltaram)")
    
    print()
    print("=" * 80)
    if validacao_1_pass and validacao_2_pass and validacao_3_pass and sempre_avancou:
        print("✅ TODAS VALIDAÇÕES PASSARAM!")
        print("   Estado está sendo persistido corretamente.")
    else:
        print("❌ ALGUMAS VALIDAÇÕES FALHARAM!")
        print("   Verifique os logs acima.")
    print("=" * 80)
    
    return validacao_1_pass and validacao_2_pass and validacao_3_pass and sempre_avancou


if __name__ == "__main__":
    success = asyncio.run(validate_state_persistence())
    exit(0 if success else 1)
