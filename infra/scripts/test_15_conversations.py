"""
Teste de 15 conversas reais do SDR W V2.

Simula cada cenário contra o prompt real do agente para avaliar:
1. Se o padrão AAB (Acknowledge, Answer, Bridge) é aplicado
2. Se as tags de mídia estão presentes
3. Se o LLM segue a postura consultiva antes do script
"""

import json
import os
import sys
import time
from pathlib import Path

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from openai import OpenAI

# ============================================
# CONFIG
# ============================================

MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")
TEMPERATURE = 0.7

# ============================================
# LOAD PROMPTS
# ============================================

prompts_dir = project_root / "app" / "agent" / "prompts"

def load_prompt(name: str) -> str:
    path = prompts_dir / name
    return path.read_text(encoding="utf-8")

system_prompt = load_prompt("system.md")
rules_prompt = load_prompt("rules.md")
stages_prompt = load_prompt("stages.md")
media_prompt = load_prompt("media.md")

# ============================================
# 15 CONVERSATIONS
# ============================================

CONVERSATIONS = [
    # ── ETAPA 1: Saudação → Diagnóstico ──
    {
        "id": 1,
        "lead": "Murilo Petrica",
        "stage": "ETAPA 1",
        "state": "NEW",
        "trigger": "800",
        "lead_response": "Captar clientes",
        "nicho": "Advogado Imobiliário",
        "test_type": "etapa1_com_resposta_desafio",
        "messages": [
            {"role": "lead", "text": "800"},
        ],
        "expected": {
            "has_audio_tag": True,
            "has_greeting": True,
            "next_state": "QUALIFYING",
        }
    },
    {
        "id": 3,
        "lead": "Jhon Uchôa",
        "stage": "ETAPA 1",
        "state": "NEW",
        "trigger": "500",
        "lead_response": "Dependo de indicação",
        "nicho": "Advogado",
        "test_type": "etapa1_gatilho_simples",
        "messages": [
            {"role": "lead", "text": "500"},
        ],
        "expected": {
            "has_audio_tag": True,
            "has_greeting": True,
            "next_state": "QUALIFYING",
        }
    },
    {
        "id": 5,
        "lead": "Stefânia Gazso",
        "stage": "ETAPA 1",
        "state": "NEW",
        "trigger": "800",
        "lead_response": "Não preciso disso",
        "nicho": "-",
        "test_type": "etapa1_rejeicao",
        "messages": [
            {"role": "lead", "text": "800"},
        ],
        "expected": {
            "has_audio_tag": True,
            "has_greeting": True,
            "next_state": "QUALIFYING",
        }
    },
    {
        "id": 6,
        "lead": "Luis Carlos Santos",
        "stage": "ETAPA 1",
        "state": "NEW",
        "trigger": "500",
        "lead_response": "Quero mais clientes",
        "nicho": "Advogado",
        "test_type": "etapa1_gatilho_simples",
        "messages": [
            {"role": "lead", "text": "500"},
        ],
        "expected": {
            "has_audio_tag": True,
            "has_greeting": True,
            "next_state": "QUALIFYING",
        }
    },
    {
        "id": 7,
        "lead": "Lucas de Godoy",
        "stage": "ETAPA 1 + PERGUNTA",
        "state": "NEW",
        "trigger": "881",
        "lead_response": "Qual o valor?",
        "nicho": "Advogado",
        "test_type": "etapa1_com_pergunta",
        "messages": [
            {"role": "lead", "text": "881. Qual o valor?"},
        ],
        "expected": {
            "has_audio_tag": True,
            "has_greeting": True,
            "aab_applied": True,
            "mentions_value_response": True,
            "next_state": "QUALIFYING",
        }
    },
    {
        "id": 8,
        "lead": "Laura Costa",
        "stage": "ETAPA 1",
        "state": "NEW",
        "trigger": "500",
        "lead_response": "Meu desafio é captar",
        "nicho": "Advogada",
        "test_type": "etapa1_gatilho_simples",
        "messages": [
            {"role": "lead", "text": "500"},
        ],
        "expected": {
            "has_audio_tag": True,
            "has_greeting": True,
            "next_state": "QUALIFYING",
        }
    },
    {
        "id": 9,
        "lead": "Matheus Ayricke",
        "stage": "ETAPA 1",
        "state": "NEW",
        "trigger": "800",
        "lead_response": "Marketing não funciona",
        "nicho": "Advogado",
        "test_type": "etapa1_gatilho_simples",
        "messages": [
            {"role": "lead", "text": "800"},
        ],
        "expected": {
            "has_audio_tag": True,
            "has_greeting": True,
            "next_state": "QUALIFYING",
        }
    },
    {
        "id": 10,
        "lead": "Jonathan Sousa",
        "stage": "ETAPA 1 + PERGUNTA",
        "state": "NEW",
        "trigger": "500",
        "lead_response": "Como funciona?",
        "nicho": "Advogado",
        "test_type": "etapa1_com_pergunta",
        "messages": [
            {"role": "lead", "text": "500. Como funciona isso?"},
        ],
        "expected": {
            "has_audio_tag": True,
            "aab_applied": True,
            "next_state": "QUALIFYING",
        }
    },
    {
        "id": 11,
        "lead": "Fernanda",
        "stage": "ETAPA 1 + PERGUNTA",
        "state": "NEW",
        "trigger": "881",
        "lead_response": "Qual o desafio?",
        "nicho": "Advogada",
        "test_type": "etapa1_com_pergunta",
        "messages": [
            {"role": "lead", "text": "881. Qual é o desafio que vocês resolvem?"},
        ],
        "expected": {
            "has_audio_tag": True,
            "aab_applied": True,
            "next_state": "QUALIFYING",
        }
    },
    {
        "id": 12,
        "lead": "Leonardo Lima",
        "stage": "ETAPA 1",
        "state": "NEW",
        "trigger": "500",
        "lead_response": "Quero saber mais",
        "nicho": "Advogado",
        "test_type": "etapa1_gatilho_simples",
        "messages": [
            {"role": "lead", "text": "Quero saber mais"},
        ],
        "expected": {
            "has_audio_tag": True,
            "has_greeting": True,
            "next_state": "QUALIFYING",
        }
    },
    {
        "id": 13,
        "lead": "Antenor Antunes",
        "stage": "ETAPA 1",
        "state": "NEW",
        "trigger": "800",
        "lead_response": "Dependo só de indicação",
        "nicho": "Advogado",
        "test_type": "etapa1_gatilho_simples",
        "messages": [
            {"role": "lead", "text": "800"},
        ],
        "expected": {
            "has_audio_tag": True,
            "has_greeting": True,
            "next_state": "QUALIFYING",
        }
    },
    # ── ETAPA 2: Diagnóstico → Metodologia ──
    {
        "id": 2,
        "lead": "Vilmar Junior",
        "stage": "ETAPA 2",
        "state": "QUALIFYING",
        "trigger": None,
        "lead_response": "Negócios Digitais",
        "nicho": "Negócios Digitais",
        "test_type": "etapa2_desafio_com_nicho",
        "messages": [
            {"role": "lead", "text": "Meu desafio é na área de negócios digitais, preciso de mais clientes"},
        ],
        "expected": {
            "has_case_tag": True,
            "has_70_30": True,
            "has_priority_question": True,
            "next_state": "QUALIFYING",
        }
    },
    {
        "id": 4,
        "lead": "Manoel Nascimento",
        "stage": "ETAPA 2",
        "state": "QUALIFYING",
        "trigger": None,
        "lead_response": "Previsibilidade de receita",
        "nicho": "Advogado",
        "test_type": "etapa2_desafio_padrao",
        "messages": [
            {"role": "lead", "text": "Meu maior desafio é ter previsibilidade de receita"},
        ],
        "expected": {
            "has_case_tag": True,
            "has_70_30": True,
            "has_priority_question": True,
            "next_state": "QUALIFYING",
        }
    },
    {
        "id": 14,
        "lead": "Rodrigo",
        "stage": "ETAPA 2 + PERGUNTA NICHO",
        "state": "QUALIFYING",
        "trigger": None,
        "lead_response": "Captar clientes. Vocês atendem criminal?",
        "nicho": "Advogado Criminalista",
        "test_type": "etapa2_desafio_com_pergunta_nicho",
        "messages": [
            {"role": "lead", "text": "Meu desafio é captar clientes, atuo na área criminal. Vocês atendem esse nicho?"},
        ],
        "expected": {
            "has_case_tag": True,
            "has_70_30": True,
            "has_priority_question": True,
            "aab_applied": True,
            "mentions_nicho": True,
            "next_state": "QUALIFYING",
        }
    },
    {
        "id": 15,
        "lead": "Rafael Galdino",
        "stage": "ETAPA 2",
        "state": "QUALIFYING",
        "trigger": None,
        "lead_response": "Desafio de captar",
        "nicho": "Advogado",
        "test_type": "etapa2_desafio_padrao",
        "messages": [
            {"role": "lead", "text": "Meu desafio é captar mais clientes, não consigo escalar"},
        ],
        "expected": {
            "has_case_tag": True,
            "has_70_30": True,
            "has_priority_question": True,
            "next_state": "QUALIFYING",
        }
    },
]


# ============================================
# STRUCTURED OUTPUT SCHEMA (simplified for test)
# ============================================

RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "agent_response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "reply_text": {"type": "string"},
                "next_state": {"type": "string"},
                "intent": {"type": "string"},
                "should_pause_ai": {"type": "boolean"},
                "should_schedule_follow": {"type": "boolean"},
                "should_call_booking_tool": {"type": "boolean"},
            },
            "required": ["reply_text", "next_state", "intent", "should_pause_ai",
                         "should_schedule_follow", "should_call_booking_tool"],
            "additionalProperties": False,
        }
    }
}


# ============================================
# EXTRACT RELEVANT STAGES
# ============================================

import re

def extract_stages_for_state(full_stages: str, state: str) -> str:
    STATE_TO_STAGES = {
        "NEW": ["etapa_1"],
        "QUALIFYING": ["etapa_2"],
    }
    stage_keys = STATE_TO_STAGES.get(state, [])
    
    SECTION_MAP = {
        "etapa_1": r"## ETAPA 1 —.*?(?=\n## ETAPA 2|---\s*\n## ETAPA 2|\Z)",
        "etapa_2": r"## ETAPA 2 —.*?(?=\n## ETAPA 3|---\s*\n## ETAPA 3|\Z)",
    }
    
    sections = []
    for key in stage_keys:
        pat = SECTION_MAP.get(key)
        if pat:
            m = re.search(pat, full_stages, re.DOTALL)
            if m:
                sections.append(m.group(0).strip())
    
    return "\n\n---\n\n".join(sections)


# ============================================
# BUILD PROMPT
# ============================================

def build_prompt(conv: dict) -> str:
    state = conv["state"]
    lead = conv["lead"]
    message = conv["messages"][-1]["text"]
    
    selective_stages = extract_stages_for_state(stages_prompt, state)
    
    system_context = json.dumps({
        "current_state": state,
        "lead_name": lead,
        "lead_id": "test-uuid",
        "no_money_flag": False,
        "has_booking": False,
    }, indent=2, ensure_ascii=False)
    
    return f"""
{system_prompt}

---

{rules_prompt}

---

## ETAPAS RELEVANTES PARA O ESTADO ATUAL

{selective_stages}

---

{media_prompt}

---

## CONTEXTO SISTÊMICO ATUAL

```json
{system_context}
```

---

## HISTÓRICO DA CONVERSA

[Sem histórico - primeira interação]

---

## MENSAGEM DO USUÁRIO

{message}

---

## SUA TAREFA

Analise o contexto acima e responda com:
1. **reply_text**: Sua resposta para o usuário (natural, conversacional).
   - **IMPORTANTE**: Se o lead fez uma PERGUNTA na mensagem (sobre nicho, área, dúvida), aplique o padrão AAB:
     - Primeiro responda a pergunta brevemente (1-2 frases, com confiança)
     - Depois conecte naturalmente com o script da etapa atual usando um conectivo ("Inclusive...", "E por falar nisso...", "Aliás...")
     - O script da etapa SEMPRE deve ser entregue completo após a resposta consultiva
   - Se o lead NÃO fez uma pergunta, siga o script da etapa normalmente
2. **next_state**: Próximo estado do lead
3. **intent**: Classificação da intenção
4. **should_pause_ai**: true/false
5. **should_schedule_follow**: true/false
6. **should_call_booking_tool**: true/false

Responda em formato JSON estruturado.
"""


# ============================================
# EVALUATE RESPONSE
# ============================================

def evaluate(conv: dict, response: dict) -> dict:
    reply = response.get("reply_text", "")
    expected = conv["expected"]
    results = {}
    
    # Check audio tag
    if "has_audio_tag" in expected:
        results["has_audio_tag"] = {
            "expected": True,
            "actual": "[MEDIA:AUDIO_PADRAO]" in reply,
            "pass": "[MEDIA:AUDIO_PADRAO]" in reply,
        }
    
    # Check case tag 
    if "has_case_tag" in expected:
        results["has_case_tag"] = {
            "expected": True,
            "actual": "[MEDIA:CASE_GENERICO]" in reply,
            "pass": "[MEDIA:CASE_GENERICO]" in reply,
        }
    
    # Check greeting
    if "has_greeting" in expected:
        name = conv["lead"].split()[0]
        has_name = name.lower() in reply.lower()
        results["has_greeting"] = {
            "expected": True,
            "actual": has_name,
            "pass": has_name,
        }
    
    # Check 70/30 mention
    if "has_70_30" in expected:
        has_70_30 = "70%" in reply or "70" in reply
        results["has_70_30"] = {
            "expected": True,
            "actual": has_70_30,
            "pass": has_70_30,
        }
    
    # Check priority question
    if "has_priority_question" in expected:
        patterns = ["prioridade", "é o que tá buscando", "é o que está buscando", "é uma prioridade"]
        has_prio = any(p.lower() in reply.lower() for p in patterns)
        results["has_priority_question"] = {
            "expected": True,
            "actual": has_prio,
            "pass": has_prio,
        }
    
    # Check AAB (consultive response before script)
    if "aab_applied" in expected:
        # AAB means there should be a substantive answer BEFORE the script
        # For etapa 1: answer before the greeting/audio
        # For etapa 2: answer mentioning the nicho before the case
        reply_lower = reply.lower()
        has_consultive = False
        
        if conv["state"] == "NEW":
            # Should have some contextual response before [MEDIA:AUDIO_PADRAO]
            audio_pos = reply.find("[MEDIA:AUDIO_PADRAO]")
            if audio_pos > 50:  # More than just "Fala João"
                has_consultive = True
        elif conv["state"] == "QUALIFYING":
            # Should mention the nicho/area before the case
            nicho = conv.get("nicho", "").lower()
            if nicho and nicho != "-":
                keywords = nicho.split()
                has_consultive = any(kw.lower() in reply_lower for kw in keywords if len(kw) > 3)
        
        results["aab_applied"] = {
            "expected": True,
            "actual": has_consultive,
            "pass": has_consultive,
        }
    
    # Check nicho mention
    if "mentions_nicho" in expected:
        nicho = conv.get("nicho", "").lower()
        keywords = [w for w in nicho.split() if len(w) > 3]
        mentioned = any(kw.lower() in reply.lower() for kw in keywords)
        results["mentions_nicho"] = {
            "expected": True,
            "actual": mentioned,
            "pass": mentioned,
        }
    
    # Check next_state
    actual_state = response.get("next_state", "")
    results["next_state"] = {
        "expected": expected["next_state"],
        "actual": actual_state,
        "pass": actual_state == expected["next_state"],
    }
    
    return results


# ============================================
# MAIN
# ============================================

def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # Try loading from .env
        env_file = project_root / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("OPENAI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    
    if not api_key:
        print("❌ OPENAI_API_KEY não encontrada")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    
    print("=" * 80)
    print(f"  TESTE DE 15 CONVERSAS REAIS — SDR W V2")
    print(f"  Modelo: {MODEL} | Temp: {TEMPERATURE}")
    print("=" * 80)
    
    all_results = []
    total_pass = 0
    total_checks = 0
    total_time = 0
    
    for conv in CONVERSATIONS:
        print(f"\n{'─' * 70}")
        print(f"  #{conv['id']} | {conv['lead']} | {conv['stage']} | State: {conv['state']}")
        print(f"  Mensagem: \"{conv['messages'][-1]['text']}\"")
        print(f"{'─' * 70}")
        
        prompt = build_prompt(conv)
        
        start = time.time()
        try:
            completion = client.chat.completions.create(
                model=MODEL,
                temperature=TEMPERATURE,
                messages=[
                    {"role": "system", "content": "Você é o SDR Agent W. Responda SEMPRE em JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format=RESPONSE_SCHEMA,
                timeout=30,
            )
            elapsed = time.time() - start
            total_time += elapsed
            
            raw = completion.choices[0].message.content
            response = json.loads(raw)
            
            # Print response
            reply = response.get("reply_text", "")
            print(f"\n  📤 RESPOSTA ({elapsed:.1f}s):")
            # Print reply in chunks
            for i, line in enumerate(reply.split("\\\\"), 1):
                line = line.strip()
                if line:
                    print(f"    [{i}] {line[:120]}{'...' if len(line)>120 else ''}")
            
            print(f"\n  🏷️  Intent: {response.get('intent')} | Next: {response.get('next_state')} | Pause: {response.get('should_pause_ai')}")
            
            # Evaluate
            results = evaluate(conv, response)
            conv_pass = sum(1 for r in results.values() if r["pass"])
            conv_total = len(results)
            total_pass += conv_pass
            total_checks += conv_total
            
            print(f"\n  📊 CHECKS ({conv_pass}/{conv_total}):")
            for check_name, check_result in results.items():
                icon = "✅" if check_result["pass"] else "❌"
                print(f"    {icon} {check_name}: expected={check_result['expected']}, actual={check_result['actual']}")
            
            all_results.append({
                "id": conv["id"],
                "lead": conv["lead"],
                "stage": conv["stage"],
                "pass": conv_pass,
                "total": conv_total,
                "elapsed": elapsed,
                "response": response,
                "checks": results,
            })
            
        except Exception as e:
            elapsed = time.time() - start
            print(f"\n  ❌ ERRO: {type(e).__name__}: {e}")
            all_results.append({
                "id": conv["id"],
                "lead": conv["lead"],
                "stage": conv["stage"],
                "pass": 0,
                "total": len(conv["expected"]),
                "elapsed": elapsed,
                "error": str(e),
            })
    
    # ============================================
    # SUMMARY
    # ============================================
    
    print("\n" + "=" * 80)
    print("  RESUMO FINAL")
    print("=" * 80)
    
    print(f"\n  Total: {total_pass}/{total_checks} checks passaram ({total_pass/total_checks*100:.0f}%)")
    print(f"  Tempo total: {total_time:.1f}s | Média: {total_time/len(CONVERSATIONS):.1f}s por conversa")
    print(f"  Modelo: {MODEL}")
    
    # Group by stage
    etapa1_results = [r for r in all_results if "ETAPA 1" in r["stage"]]
    etapa2_results = [r for r in all_results if "ETAPA 2" in r["stage"]]
    
    e1_pass = sum(r["pass"] for r in etapa1_results)
    e1_total = sum(r["total"] for r in etapa1_results)
    e2_pass = sum(r["pass"] for r in etapa2_results)
    e2_total = sum(r["total"] for r in etapa2_results)
    
    print(f"\n  📍 Etapa 1: {e1_pass}/{e1_total} ({e1_pass/e1_total*100:.0f}%)" if e1_total else "")
    print(f"  📍 Etapa 2: {e2_pass}/{e2_total} ({e2_pass/e2_total*100:.0f}%)" if e2_total else "")
    
    # AAB specific
    aab_results = [r for r in all_results if "checks" in r and "aab_applied" in r.get("checks", {})]
    if aab_results:
        aab_pass = sum(1 for r in aab_results if r["checks"]["aab_applied"]["pass"])
        print(f"\n  🎯 AAB (Postura Consultiva): {aab_pass}/{len(aab_results)} ({aab_pass/len(aab_results)*100:.0f}%)")
    
    # Failures
    failures = [r for r in all_results if "checks" in r and any(not c["pass"] for c in r["checks"].values())]
    if failures:
        print(f"\n  ⚠️  FALHAS DETECTADAS:")
        for r in failures:
            failed_checks = [name for name, c in r["checks"].items() if not c["pass"]]
            print(f"    #{r['id']} {r['lead']}: {', '.join(failed_checks)}")
    else:
        print(f"\n  🎉 TODAS AS CONVERSAS PASSARAM!")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
