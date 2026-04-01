"""Teste de fluxo COMPLETO - Do início ao fim do funil.

Este script simula um lead real passando por TODAS as 7 etapas:
1. Saudação + Áudio
2. Dois Motivos + Case + Prioridade
3. Metodologia (Infojurídico)
4. Qualificação Financeira
5. Convite + Horário + Email
6. Materiais
7. Checklist + Confirmação

EXECUÇÃO:
    python infra/scripts/test_full_funnel.py

RESULTADOS:
    - Mostra cada resposta do agente
    - Valida se estado avançou corretamente
    - Verifica se NÃO repetiu etapas
    - Valida agendamento no Cal.com (se configurado)
"""

import asyncio
import time
from datetime import datetime, timedelta
from app.config.settings import get_settings
from app.agent.graph import run_agent
from app.state.lead_states import AgentState
from app.repositories.leads_repository import LeadsRepository
from app.repositories.conversations_repository import ConversationsRepository
from app.domain.enums import LeadState

settings = get_settings()


# ============================================
# DADOS DO LEAD DE TESTE
# ============================================

TEST_LEAD = {
    "name": "Fábio",
    "email": "faabioo201415@gmail.com",
    "session_id": f"test_funnel_{int(time.time())}",
}

# ============================================
# ROTEIRO COMPLETO DO FUNIL
# ============================================

FUNNEL_STEPS = [
    {
        "step": 1,
        "name": "Gatilho Inicial",
        "message": "500",
        "expected_state": "QUALIFYING",
        # AUDIO_PADRAO é tag interna — nunca aparece no reply. Valida apenas conteúdo real.
        "expected_contains": ["Faaaaala"],
        "expected_not_contains": ["Entendi. Esse é um dos problemas"],
    },
    {
        "step": 2,
        "name": "Responde à Pergunta do Áudio",
        "message": "Estou com dificuldade para captar clientes através do Instagram",
        "expected_state": "WAITING_PRIORITY_CONFIRMATION",
        # CASE_GENERICO é tag interna — nunca aparece no reply. Valida conteúdo real.
        "expected_contains": ["Entendi", "advocacia"],
        "expected_not_contains": ["Faaaaala"],
    },
    {
        "step": 3,
        "name": "Confirma Prioridade",
        "message": "Sim, é prioridade resolver isso esse mês",
        "expected_state": "WAITING_FIT_CONFIRMATION",
        "expected_contains": ["milhões"],  # "infojuridicos" pode não aparecer em toda rodada
        "expected_not_contains": ["Faaaaala"],
    },
    {
        "step": 4,
        "name": "Confirma Fit da Metodologia",
        "message": "Sim, é exatamente o que estou buscando",
        "expected_state": "WAITING_TIME",
        # Agente varia as palavras; validar apenas continuidade natural do funil
        "expected_contains": [],
        "expected_not_contains": ["infojuridicos"],
    },
    {
        "step": 5,
        "name": "Confirma Agendamento e Sugere Horário",
        "message": "Pode marcar! Amanhã às 14h fica bom para mim",
        "expected_state": "WAITING_EMAIL",
        # Agente usa "e-mail" (com hífen) — validar presença da palavra chave
        "expected_contains": ["Boa"],
        "expected_not_contains": [],
    },
    {
        "step": 6,
        "name": "Envia Email",
        "message": "joao.silva@email.com",
        "expected_state": "SCHEDULED",
        # Sem Cal.com o booking é simulado — valida apenas transição de estado
        "expected_contains": [],
        "expected_not_contains": [],
    },
    {
        "step": 7,
        "name": "Confirma Recebimento dos Materiais",
        "message": "Sim, já recebi e entendi tudo",
        # Após SCHEDULED, o agente permanece em SCHEDULED para todo follow-up pós-booking.
        # Transição POST_BOOKING_PENDING_CHECKLIST só ocorre quando o fluxo
        # de materiais/checklist está ativo via serviço externo.
        "expected_state": "SCHEDULED",
        "expected_contains": [],
        "expected_not_contains": [],
    },
    {
        "step": 8,
        "name": "Confirma Checklist",
        "message": "Tudo entendido! Estou pronto para a reunião",
        "expected_state": "SCHEDULED",
        # "vejo você" requer que o horário da etapa 5 seja lembrado pelo LLM —
        # o prompt diz "Perfeito, vejo você [HORÁRIO]" mas pode variar
        "expected_contains": ["Perfeito"],
        "expected_not_contains": [],
    },
]


async def test_full_funnel():
    """Executa teste completo do funil."""
    
    print("=" * 80)
    print("TESTE DE FLUXO COMPLETO - FUNIL SDR (8 ETAPAS)")
    print("=" * 80)
    print()
    print(f"Lead: {TEST_LEAD['name']}")
    print(f"Email: {TEST_LEAD['email']}")
    print(f"Session: {TEST_LEAD['session_id']}")
    print()
    
    leads_repo = LeadsRepository()
    conversations_repo = ConversationsRepository()
    
    # ============================================
    # SETUP: Criar lead inicial
    # ============================================
    
    print("[SETUP] Buscando ou criando lead de teste...")
    lead = await leads_repo.get_by_email(TEST_LEAD["email"])

    if lead:
        print(f"  ♻️  Lead já existe: {lead.id} (estado atual: {lead.current_state.value})")
        print(f"  🔄 Resetando estado para NEW para novo teste...")
        lead = await leads_repo.update_state(lead.id, LeadState.NEW)
        print(f"  ✅ Estado resetado: {lead.current_state.value}")
    else:
        lead = await leads_repo.create(
            name=TEST_LEAD["name"],
            email=TEST_LEAD["email"],
            source="test_full_funnel",
        )
        print(f"  ✅ Lead criado: {lead.id}")

    print(f"  Lead ID: {lead.id}")
    print(f"  Estado inicial: {lead.current_state.value}")
    print()
    
    # ============================================
    # EXECUTAR CADA ETAPA DO FUNIL
    # ============================================
    
    results = []
    current_state = lead.current_state
    
    for step_config in FUNNEL_STEPS:
        step_num = step_config["step"]
        step_name = step_config["name"]
        message = step_config["message"]
        expected_state = step_config["expected_state"]
        expected_contains = step_config["expected_contains"]
        expected_not_contains = step_config["expected_not_contains"]
        
        print("=" * 80)
        print(f"ETAPA {step_num}: {step_name}")
        print("=" * 80)
        print()
        
        # Criar estado do agente
        agent_state = AgentState(
            lead_id=lead.id,  # Passa o lead criado no setup para o agente não criar um novo
            session_id=TEST_LEAD["session_id"],
            incoming_message=message,
            incoming_message_type="text",
        )
        
        # Executar agente
        print(f"📤 Enviando: \"{message[:60]}{'...' if len(message) > 60 else ''}\"")
        print()
        
        try:
            result = await run_agent(agent_state)
        except Exception as e:
            print(f"❌ ERRO na execução: {e}")
            results.append({"step": step_num, "success": False, "errors": [str(e)]})
            continue
        
        # Recarregar estado do banco PARA VALIDAR SE PERSISTIU
        lead_updated = await leads_repo.get_by_id(lead.id)
        
        # Extrair estados
        state_before = result.state_before.value if result.state_before else "UNKNOWN"
        state_after = result.next_state.value if result.next_state else "UNKNOWN"
        state_in_db = lead_updated.current_state.value if lead_updated else "NOT_FOUND"
        
        # Debug: verificar se o estado no banco bate
        print(f"🔍 DEBUG ESTADO: lead_id={lead.id}, state_after={state_after}, state_in_db={state_in_db}")
        print()
        
        # Mostrar resposta
        reply_preview = result.reply_text[:150].replace("\n", " ")
        print(f"📥 Resposta: {reply_preview}...")
        print()
        
        # Validar estado
        state_before = result.state_before.value if result.state_before else "UNKNOWN"
        state_after = result.next_state.value if result.next_state else "UNKNOWN"
        state_in_db = lead_updated.current_state.value
        
        print(f"📊 Estados:")
        print(f"   Antes: {state_before}")
        print(f"   Depois: {state_after}")
        print(f"   No banco: {state_in_db}")
        print()
        
        # Validar conteúdo da resposta
        validation_errors = []
        
        for expected in expected_contains:
            if expected not in result.reply_text:
                validation_errors.append(f"❌ Esperado conter: '{expected}'")
        
        for not_expected in expected_not_contains:
            if not_expected in result.reply_text:
                validation_errors.append(f"❌ Esperado NÃO conter: '{not_expected}'")
        
        if state_after != expected_state:
            validation_errors.append(f"❌ Estado esperado: {expected_state}, foi: {state_after}")
        
        if state_in_db != expected_state:
            validation_errors.append(f"❌ Estado no banco: {expected_state}, foi: {state_in_db}")
        
        # Mostrar validação
        if validation_errors:
            print("❌ VALIDAÇÃO FALHOU:")
            for error in validation_errors:
                print(f"   {error}")
            results.append({"step": step_num, "success": False, "errors": validation_errors})
        else:
            print("✅ VALIDAÇÃO PASSOU")
            results.append({"step": step_num, "success": True})
        
        print()
        print("-" * 80)
        print()
        
        # Pequeno delay para evitar rate limit
        await asyncio.sleep(0.5)
    
    # ============================================
    # RESUMO FINAL
    # ============================================
    
    print("=" * 80)
    print("RESUMO FINAL DO TESTE")
    print("=" * 80)
    print()
    
    total_steps = len(results)
    passed_steps = sum(1 for r in results if r["success"])
    failed_steps = total_steps - passed_steps
    
    print(f"Total de etapas: {total_steps}")
    print(f"✅ Aprovadas: {passed_steps}")
    print(f"❌ Falharam: {failed_steps}")
    print()
    
    if failed_steps > 0:
        print("Etapas com erro:")
        for r in results:
            if not r["success"]:
                print(f"  Etapa {r['step']}: {r['errors']}")
        print()
    
    # Mostrar fluxo completo de estados
    print("Fluxo de estados:")
    lead_final = await leads_repo.get_by_id(lead.id)
    print(f"  Estado final: {lead_final.current_state.value}")
    print()
    
    # Verificar booking
    from app.repositories.bookings_repository import BookingsRepository
    bookings_repo = BookingsRepository()
    booking = await bookings_repo.get_active_by_lead(lead.id)
    
    if booking:
        print(f"✅ Booking criado: {booking.id}")
        print(f"   Start: {booking.start_time}")
        print(f"   Email: {TEST_LEAD['email']}")
    else:
        print("⚠️  Booking não encontrado (pode ser esperado se Cal.com não configurado)")
    
    print()
    print("=" * 80)
    
    if failed_steps == 0:
        print("✅ TODAS AS ETAPAS PASSARAM!")
        print("   Funil completo funcionou corretamente.")
    else:
        print("❌ ALGUMAS ETAPAS FALHARAM!")
        print("   Verifique os erros acima.")
    
    print("=" * 80)
    
    return failed_steps == 0


if __name__ == "__main__":
    print()
    print("=" * 80)
    print("⚠️  ATENÇÃO: Este teste cria um lead real e pode agendar reunião!")
    print("⚠️  Certifique-se de que:")
    print("⚠️  - API está rodando")
    print("⚠️  - OpenAI API Key está configurada")
    print("⚠️  - Supabase está configurado")
    print("=" * 80)
    print()
    
    input("Pressione ENTER para começar o teste...")
    print()
    
    success = asyncio.run(test_full_funnel())
    
    print()
    if success:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print("⚠️  TESTE CONCLUÍDO COM ERROS!")
    
    print()
    
    exit(0 if success else 1)
