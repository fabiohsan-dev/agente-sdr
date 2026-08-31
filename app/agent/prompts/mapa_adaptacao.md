# MAPA DE ADAPTAÇÃO DO PROMPT COMERCIAL

## Documento Técnico de Adaptação
**Data:** 2026-03-31  
**Versão:** 1.0  
**Stack Original:** n8n + Chatwoot  
**Stack Destino:** Python + FastAPI + LangGraph + Supabase + Cal.com

---

## 1. O QUE PERMANECEU NO PROMPT

### Identidade e Tom
- ✅ Identidade do time W.
- ✅ Missão e propósito
- ✅ Tom entusiástico, confiante, leve
- ✅ Uso de "kk", reticências
- ✅ Proibições de vocabulário (funil, ROI, etc.)

### Estrutura Comercial
- ✅ Etapas 1→7 completas
- ✅ Gates de cada etapa
- ✅ Fluxo de qualificação
- ✅ AERP (Afirmação → Explicação → Reenquadramento → Pergunta)
- ✅ Regra de recuperação pós-AERP

### Conteúdo Específico
- ✅ Scripts literais de cada etapa
- ✅ Tabela de objeções rápidas
- ✅ Situações especiais
- ✅ Gatilhos de entrada (500, 800, 881, etc.)
- ✅ Cases e exemplos (Sérgio, 60mil/mês)
- ✅ Valores (2 mil, 60 mil)
- ✅ Links de materiais (Case study, Google Drive)

### Regras de Linguagem
- ✅ Máx. 3 frases por balão
- ✅ UMA pergunta por mensagem
- ✅ Separador `\\` para novos balões
- ✅ Múltiplos balões permitidos (Etapa 2, 6, 7)

### Mídia
- ✅ Tags `[MEDIA:AUDIO_PADRAO]` e `[MEDIA:CASE_GENERICO]`
- ✅ Regras de uso de mídia
- ✅ Comportamento com áudio do lead

### Agendamento (Nível Conversacional)
- ✅ Lógica de coleta de horário
- ✅ Regra de 3 opções máximas
- ✅ Proibição de lista com quebras
- ✅ Fluxo: horário → email → confirmação
- ✅ Modo pós-agendamento

---

## 2. O QUE FOI ADAPTADO

### Contexto Operacional

**ORIGINAL (n8n):**
```
{{ $now.format('dd/MM/yyyy') }}
{{ $('Dados').item.json.instagram_sender_id }}
{{ $('Set Perfil IG').item.json.ig_profile.name }}
{{ $now.setZone("America/Sao_Paulo").toFormat("yyyy-MM-dd") }}
```

**ADAPTADO (LangGraph):**
```
{{ current_date }}
{{ lead.instagram_id }}
{{ lead.name }}
{{ today_sp }}
{{ tomorrow_sp }}
```

**Justificativa:** Remover dependência de sintaxe n8n ($(), $now). Usar placeholders genéricos injetados pelo Python.

---

### Tools

**ORIGINAL (n8n):**
- `Think3` (tool interna)
- `RAG SUPABASE` (tool)
- `Agente de agendamento` (tool Cal.com)
- `Buscar contexto do lead` (tool)

**ADAPTADO (LangGraph):**
- **Think3** → Incorporado como processo interno do node `generate_reply`
- **RAG** → Contexto injetado via `conversation_context` e `recent_messages`
- **Agendamento** → Flags: `should_call_booking_tool`, `booking_confirmed`
- **Contexto do lead** → Já vem em `state.lead`, `state.current_state`

**Justificativa:** LangGraph não tem "tools" no mesmo sentido do n8n. O fluxo é controlado pelos nodes e o output é estruturado.

---

### Referências a Dados

**ORIGINAL:**
```
{{ $('Dados').item.json.ig_profile.name }}
{{ $('Set Perfil IG').item.json.ig_profile.name }}
```

**ADAPTADO:**
```
{{ lead.name }}
{{ lead.instagram_id }}
```

**Justificativa:** Simplificar para variáveis de template padrão.

---

### Controle de Tempo

**ORIGINAL:**
```
{{ $now.setZone("America/Sao_Paulo").toFormat("yyyy-MM-dd") }}
{{ $now.setZone("America/Sao_Paulo").plus({ days: 1 }).toFormat("yyyy-MM-dd") }}
```

**ADAPTADO:**
```
{{ today_sp }}
{{ tomorrow_sp }}
```

**Justificativa:** Sistema Python calcula e injeta valores prontos.

---

### Confirmação de Agendamento

**ORIGINAL:**
```
Acionar `Agente de agendamento` → criar evento
Retorno: bookingUid
```

**ADAPTADO:**
```
should_call_booking_tool: true
booking_confirmed: true (via metadata)
```

**Justificativa:** LangGraph usa flags estruturadas, não chamadas de tool explícitas no prompt.

---

## 3. O QUE SAIU DO PROMPT E VIROU REGRA HARD NO CÓDIGO

### 3.1 Trava Financeira

**ANTES (apenas no prompt):**
```
"Sem dinheiro" → "Entendi! Quando for o momento, é só chamar aqui. Abraço!"
```

**AGORA (código + prompt):**

**Código (`app/state/guards.py`):**
```python
def can_offer_booking(state: AgentState) -> bool:
    if state.no_money_flag:
        return False
    if state.current_state == LeadState.NO_MONEY:
        return False
    return True
```

**Prompt:** Mantém instrução conversacional, mas código bloqueia fisicamente.

**Estado:** `LeadState.NO_MONEY`

---

### 3.2 Owner Mode (Agent/Human)

**ANTES (inexistente):**
- Sem controle de handoff

**AGORA (código):**

**Código (`app/state/guards.py`):**
```python
def should_agent_respond(state: AgentState) -> bool:
    if state.owner_mode == "human":
        return False
    if state.current_state == LeadState.PAUSED_BY_HUMAN:
        return False
    return True
```

**Estado:** `OwnerMode.AGENT` ou `OwnerMode.HUMAN`

---

### 3.3 Cancelamento de Follow-up

**ANTES (apenas no prompt):**
- Sem menção

**AGORA (código):**

**Código (`app/state/guards.py`):**
```python
def should_cancel_follow_on_response(state: AgentState) -> bool:
    return state.incoming_message is not None
```

**Ação:** `actions.append("cancel_follow")`

---

### 3.4 Bloqueio de Reinício de Roteiro

**ANTES (apenas no prompt):**
```
"NUNCA REINICIAR O ROTEIRO"
```

**AGORA (código + prompt):**

**Código (`app/state/guards.py`):**
```python
def should_restart_commercial_script(state: AgentState) -> bool:
    if state.current_state == LeadState.SCHEDULED:
        return False
    return True
```

**Metadata:** `state.metadata["restart_script_blocked"] = True`

---

### 3.5 Estado do Lead e Transições

**ANTES (implícito no prompt):**
- Etapas 1→7, mas sem estado explícito

**AGORA (código):**

**Código (`app/domain/enums.py`):**
```python
class LeadState(str, Enum):
    NEW = "NEW"
    QUALIFYING = "QUALIFYING"
    WAITING_PRIORITY_CONFIRMATION = "WAITING_PRIORITY_CONFIRMATION"
    WAITING_FIT_CONFIRMATION = "WAITING_FIT_CONFIRMATION"
    WAITING_TIME = "WAITING_TIME"
    WAITING_EMAIL = "WAITING_EMAIL"
    BOOKING_IN_PROGRESS = "BOOKING_IN_PROGRESS"
    SCHEDULED = "SCHEDULED"
    POST_BOOKING_PENDING_MATERIALS = "POST_BOOKING_PENDING_MATERIALS"
    POST_BOOKING_PENDING_CHECKLIST = "POST_BOOKING_PENDING_CHECKLIST"
    NO_MONEY = "NO_MONEY"
    CLOSED = "CLOSED"
    PAUSED_BY_HUMAN = "PAUSED_BY_HUMAN"
```

**Matriz de transições:** `app/state/transitions.py`

---

### 3.6 Envio de Materiais e Checklist

**ANTES (apenas no prompt):**
```
Etapa 6 → Enviar materiais
Etapa 7 → Enviar checklist
```

**AGORA (código + prompt):**

**Código (`app/agent/models/structured_outputs.py`):**
```python
should_send_materials: bool
should_send_checklist: bool
```

**Ações:** `actions.append("send_materials")`, `actions.append("send_checklist")`

---

### 3.7 Decisão de Resposta

**ANTES (implícito):**
- Agente sempre responde

**AGORA (código):**

**Código (`app/state/guards.py`):**
```python
def should_agent_respond(state: AgentState) -> bool:
    if state.owner_mode == "human":
        return False
    if state.current_state == LeadState.PAUSED_BY_HUMAN:
        return False
    return True
```

**Resultado:** `state.reply_text = None` se bloqueado

---

### 3.8 Persistência de Dados Operacionais

**ANTES (n8n workflow):**
- Dados voláteis no workflow

**AGORA (Supabase):**

**Tabelas:**
- `leads` → `current_state`, `owner_mode`, `no_money_flag`, `has_booking`
- `conversations` → `session_id`, `last_message_at`
- `bookings` → `booking_uid`, `start_time`, `status`
- `follow_jobs` → `scheduled_for`, `status`
- `media_assets` → `cdn_url`, `transcription`, `analysis`
- `agent_snapshots` → `state_before`, `state_after`, `reply_text`, `actions`

---

## 4. CONTEXTO NECESSÁRIO DO BACKEND

### Variáveis Injetadas no Prompt

| Variável | Tipo | Origem | Descrição |
|----------|------|--------|-----------|
| `current_date` | string | `datetime.now()` | Data atual formatada (dd/MM/yyyy) |
| `lead.id` | UUID | `state.lead.id` | ID único do lead |
| `lead.name` | string | `state.lead.name` | Nome do lead |
| `lead.email` | string | `state.lead.email` | Email do lead |
| `lead.instagram_id` | string | `state.lead.custom_fields` | Instagram sender ID |
| `today_sp` | string | `datetime.now(SP)` | Hoje em SP (yyyy-MM-dd) |
| `tomorrow_sp` | string | `datetime.now(SP) + 1d` | Amanhã em SP (yyyy-MM-dd) |
| `current_state` | string | `state.current_state.value` | Estado atual do lead |
| `owner_mode` | string | `state.owner_mode.value` | "agent" ou "human" |
| `has_booking` | boolean | `state.has_booking` | Lead tem agendamento? |
| `booking_uid` | string | `state.metadata` | UID do booking no Cal.com |
| `materials_sent` | boolean | `state.materials_sent` | Materiais já enviados? |
| `checklist_sent` | boolean | `state.checklist_sent` | Checklist já enviado? |
| `latest_media_type` | string | `state.media_type` | "audio" ou "image" |
| `latest_media_url` | string | `state.media_url` | URL da CDN |
| `latest_media_analysis` | string | `state.media_transcription` ou `state.media_analysis` | Transcrição ou análise |

---

### Output Estruturado Esperado

O sistema espera do LLM:

```python
AgentStructuredOutput(
    reply_text: str,              # Resposta para o usuário
    next_state: LeadState,        # Próximo estado
    actions: list[str],           # Ações a executar
    should_schedule_follow: bool, # Agendar follow-up?
    should_call_booking_tool: bool, # Acionar agendamento?
    should_send_materials: bool,  # Enviar materiais?
    should_send_checklist: bool,  # Enviar checklist?
    follow_reason: str | None,    # Motivo do follow
    booking_context: str | None,  # Contexto do booking
)
```

---

## 5. FLUXO DE EXECUÇÃO NO LANGGRAPH

```
1. ingest_message
   ↓
2. load_state (busca lead, conversation, messages)
   ↓
3. apply_hard_rules (aplica guards do código)
   ↓
4. maybe_process_media (transcreve áudio, analisa imagem)
   ↓
5. classify_intent (classifica intenção do lead)
   ↓
6. decide_stage (decide próximo estado e ações)
   ↓
7. maybe_call_tools (prepara flags de tools)
   ↓
8. generate_reply (USA PROMPT ADAPTADO + contexto)
   ↓
9. persist_decision (salva snapshot, atualiza lead)
   ↓
10. finalize (valida e limpa)
```

**O prompt adaptado é usado principalmente no node 8 (`generate_reply`).**

---

## 6. RESUMO DAS MUDANÇAS

| Categoria | Antes (n8n) | Depois (LangGraph) |
|-----------|-------------|---------------------|
| **Contexto** | Variáveis n8n ($(), $now) | Placeholders Python ({{ }}) |
| **Tools** | 4 tools explícitas | Flags estruturadas + nodes |
| **Estado** | Implícito no workflow | Explícito (LeadState enum) |
| **Regras** | Apenas no prompt | Prompt + código (guards) |
| **Dados** | Voláteis no workflow | Persistidos no Supabase |
| **Mídia** | Processamento n8n | Serviços Python + CDN |
| **Agendamento** | Tool Cal.com no n8n | Service Python + Cal.com API |
| **Output** | JSON do n8n | AgentStructuredOutput |

---

## 7. COMPATIBILIDADE

### ✅ Preservado
- Identidade e tom original
- Todas as 7 etapas
- Gates e regras de progressão
- AERP completo
- Objeções e situações especiais
- Tags de mídia
- Scripts literais

### ✅ Adaptado
- Contexto operacional (sem n8n)
- Tools → Flags sistêmicas
- Estado → Enums + código
- Output → Estruturado para LangGraph

### ✅ Melhorado
- Regras hard no código (mais confiável)
- Estado explícito (mais rastreável)
- Persistência completa (debug)
- Mídia em CDN (escalável)
- Owner mode (handoff futuro)

---

## 8. PRÓXIMOS PASSOS

1. **Testar prompt adaptado** no playground
2. **Validar gates** e transições de estado
3. **Ajustar tom** se necessário
4. **Implementar processamento real de mídia** (Whisper, GPT-4 Vision)
5. **Adicionar RAG** para objeções complexas (Playbooks 02-05)
6. **Integrar Chatwoot** (Phase 2)

---

**FIM DO DOCUMENTO DE ADAPTAÇÃO**
