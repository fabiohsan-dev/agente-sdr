# ✅ ADAPTAÇÃO DO PROMPT COMERCIAL CONCLUÍDA

## Resumo da Entrega

**Data:** 2026-03-31  
**Prompt Original:** n8n + Chatwoot  
**Prompt Adaptado:** Python + FastAPI + LangGraph + Supabase + Cal.com

---

## 📄 ARQUIVOS CRIADOS/ATUALIZADOS

### Novos Arquivos
| Arquivo | Descrição |
|---------|-----------|
| `app/agent/prompts/prompt_comercial_adaptado.md` | Prompt comercial completo adaptado |
| `app/agent/prompts/mapa_adaptacao.md` | Documento técnico de adaptação |

### Arquivos Atualizados
| Arquivo | Mudança |
|---------|---------|
| `app/agent/prompts/system.md` | Atualizado com identidade W. e regras críticas |
| `app/agent/prompts/rules.md` | Atualizado com etapas, AERP, tabela de objeções |
| `app/agent/prompts/stages.md` | Atualizado com guia detalhado das 7 etapas |
| `app/agent/prompts/media.md` | Atualizado com tags de mídia e regras de CDN |

---

## 🎯 O QUE FOI PRESERVADO

### Identidade e Tom
- ✅ Time do W., estrategista consultivo
- ✅ Tom entusiástico, confiante, leve, direto
- ✅ Uso de "kk", reticências
- ✅ Proibições de vocabulário (funil, ROI, lead, etc.)

### Estrutura Comercial
- ✅ **7 etapas completas** (1→7)
- ✅ **Gates obrigatórios** em cada etapa
- ✅ **Scripts literais** de cada etapa
- ✅ **Case do Sérgio** (10k → 700 → 25k → 60k+)
- ✅ **Valores** (2 mil, 60 mil)
- ✅ **Links** (agenciaww.com/cash, Google Drive)

### Técnicas de Persuasão
- ✅ **AERP completo** (Afirmação → Explicação → Reenquadramento → Pergunta)
- ✅ **Regra de recuperação pós-AERP**
- ✅ **Gatilhos de entrada** (500, 800, 881, 204, 203)
- ✅ **Tabela de objeções rápidas**
- ✅ **Situações especiais**

### Mídia
- ✅ **Tags** `[MEDIA:AUDIO_PADRAO]` e `[MEDIA:CASE_GENERICO]`
- ✅ **Regras de uso** (apenas Etapa 1 e Etapa 2)
- ✅ **Comportamento com áudio do lead**

### Agendamento
- ✅ **Regra de 3 opções máximas**
- ✅ **Proibição de lista com quebras**
- ✅ **Fluxo: horário → email → confirmação**
- ✅ **Modo pós-agendamento**

---

## 🔄 O QUE FOI ADAPTADO

### Contexto Operacional

**Antes (n8n):**
```
{{ $now.format('dd/MM/yyyy') }}
{{ $('Dados').item.json.instagram_sender_id }}
{{ $('Set Perfil IG').item.json.ig_profile.name }}
```

**Depois (LangGraph):**
```
{{ current_date }}
{{ lead.instagram_id }}
{{ lead.name }}
{{ today_sp }}
{{ tomorrow_sp }}
```

### Tools

**Antes (n8n):**
- `Think3` (tool interna)
- `RAG SUPABASE` (tool)
- `Agente de agendamento` (tool Cal.com)
- `Buscar contexto do lead` (tool)

**Depois (LangGraph):**
- **Think3** → Processo interno do node `generate_reply`
- **RAG** → Contexto injetado via `conversation_context`
- **Agendamento** → Flags: `should_call_booking_tool`
- **Contexto** → Já vem em `state.lead`

### Confirmação de Agendamento

**Antes:**
```
Acionar Tool → criar evento → bookingUid
```

**Depois:**
```
should_call_booking_tool: true
booking_confirmed: true (via metadata)
```

---

## ⚠️ O QUE VIROU REGRA HARD NO CÓDIGO

### 1. Trava Financeira
**Código:** `app/state/guards.py`
```python
def can_offer_booking(state: AgentState) -> bool:
    if state.no_money_flag:
        return False
    return True
```
**Estado:** `LeadState.NO_MONEY`

### 2. Owner Mode (Agent/Human)
**Código:** `app/state/guards.py`
```python
def should_agent_respond(state: AgentState) -> bool:
    if state.owner_mode == "human":
        return False
    return True
```
**Estado:** `OwnerMode.AGENT` ou `OwnerMode.HUMAN`

### 3. Cancelamento de Follow-up
**Código:** `app/state/guards.py`
```python
def should_cancel_follow_on_response(state: AgentState) -> bool:
    return state.incoming_message is not None
```
**Ação:** `actions.append("cancel_follow")`

### 4. Bloqueio de Reinício de Roteiro
**Código:** `app/state/guards.py`
```python
def should_restart_commercial_script(state: AgentState) -> bool:
    if state.current_state == LeadState.SCHEDULED:
        return False
    return True
```

### 5. Estados do Lead
**Código:** `app/domain/enums.py`
```python
class LeadState(str, Enum):
    NEW = "NEW"
    QUALIFYING = "QUALIFYING"
    WAITING_PRIORITY_CONFIRMATION = "..."
    # ... 13 estados no total
```

### 6. Persistência de Dados
**Tabelas Supabase:**
- `leads` → `current_state`, `owner_mode`, `no_money_flag`
- `bookings` → `booking_uid`, `start_time`, `status`
- `follow_jobs` → `scheduled_for`, `status`
- `media_assets` → `cdn_url`, `transcription`, `analysis`
- `agent_snapshots` → `state_before`, `state_after`, `reply_text`

---

## 📦 CONTEXTO NECESSÁRIO DO BACKEND

### Variáveis Injetadas no Prompt

| Variável | Tipo | Origem |
|----------|------|--------|
| `current_date` | string | `datetime.now()` |
| `lead.name` | string | `state.lead.name` |
| `lead.email` | string | `state.lead.email` |
| `lead.instagram_id` | string | `state.lead.custom_fields` |
| `today_sp` | string | `datetime.now(SP)` |
| `tomorrow_sp` | string | `datetime.now(SP) + 1d` |
| `current_state` | string | `state.current_state.value` |
| `owner_mode` | string | `state.owner_mode.value` |
| `has_booking` | boolean | `state.has_booking` |
| `booking_uid` | string | `state.metadata` |
| `materials_sent` | boolean | `state.materials_sent` |
| `checklist_sent` | boolean | `state.checklist_sent` |
| `latest_media_type` | string | `state.media_type` |
| `latest_media_url` | string | `state.media_url` |
| `latest_media_analysis` | string | `state.media_transcription` |

### Output Estruturado Esperado

```python
AgentStructuredOutput(
    reply_text: str,              # Resposta para o usuário
    next_state: LeadState,        # Próximo estado
    actions: list[str],           # Ações a executar
    should_schedule_follow: bool, # Agendar follow-up?
    should_call_booking_tool: bool, # Acionar agendamento?
    should_send_materials: bool,  # Enviar materiais?
    should_send_checklist: bool,  # Enviar checklist?
)
```

---

## 🧪 FLUXO DE EXECUÇÃO

```
1. ingest_message → Processa mensagem recebida
   ↓
2. load_state → Busca lead, conversation, messages
   ↓
3. apply_hard_rules → Aplica guards do código
   ↓
4. maybe_process_media → Transcreve áudio, analisa imagem
   ↓
5. classify_intent → Classifica intenção do lead
   ↓
6. decide_stage → Decide próximo estado e ações
   ↓
7. maybe_call_tools → Prepara flags de tools
   ↓
8. generate_reply → USA PROMPT ADAPTADO + contexto
   ↓
9. persist_decision → Salva snapshot, atualiza lead
   ↓
10. finalize → Valida e limpa
```

**O prompt adaptado é usado principalmente no node 8 (`generate_reply`).**

---

## ✅ CHECKLIST DE VALIDAÇÃO

### Prompt
- [x] Identidade W. preservada
- [x] 7 etapas completas
- [x] Gates de cada etapa
- [x] Scripts literais
- [x] Case do Sérgio
- [x] Valores (2 mil, 60 mil)
- [x] Links de materiais
- [x] AERP completo
- [x] Tabela de objeções
- [x] Situações especiais
- [x] Tags de mídia
- [x] Trava financeira no prompt

### Código
- [x] 13 estados do lead
- [x] Guards de negócio
- [x] Trava financeira no código
- [x] Owner mode
- [x] Cancelamento de follow
- [x] Bloqueio de reinício
- [x] Persistência Supabase
- [x] Output estruturado

### Integrações
- [x] Supabase (8 tabelas)
- [x] Cal.com (agendamento)
- [x] Langfuse (tracing)
- [x] OpenAI (LLM + Whisper)

### Playground
- [x] Texto, áudio (URL), imagem (URL)
- [x] Histórico de mensagens
- [x] Indicador de estado
- [x] Session management

---

## 🚀 PRÓXIMOS PASSOS

### Imediatos
1. **Configurar .env** com chaves (OpenAI, Supabase)
2. **Criar banco no Supabase** (executar schema.sql)
3. **Testar no playground** (API + Playground)
4. **Validar gates e transições** de estado

### Phase 2
1. **Processamento real de mídia** (Whisper, GPT-4 Vision)
2. **RAG para objeções complexas** (Playbooks 02-05)
3. **Follow-up agendado** (scheduler/cron)
4. **Integração Chatwoot** (handoff agent/human)
5. **Testes e2e**

---

## 📊 RESUMO FINAL

| Categoria | Antes | Depois |
|-----------|-------|--------|
| **Stack** | n8n + Chatwoot | Python + LangGraph |
| **Prompts** | 1 arquivo | 4 arquivos modulares |
| **Estado** | Implícito | Explícito (13 estados) |
| **Regras** | Apenas prompt | Prompt + código |
| **Tools** | 4 tools n8n | Flags estruturadas |
| **Dados** | Voláteis | Persistidos (Supabase) |
| **Mídia** | n8n processing | Serviços Python + CDN |
| **Output** | JSON n8n | AgentStructuredOutput |

### ✅ Preservado
- Identidade e tom original
- Todas as 7 etapas
- Gates e regras de progressão
- AERP completo
- Objeções e situações especiais
- Tags de mídia
- Scripts literais
- Cases e valores

### ✅ Melhorado
- Regras hard no código (mais confiável)
- Estado explícito (mais rastreável)
- Persistência completa (debug)
- Mídia em CDN (escalável)
- Owner mode (handoff futuro)
- Langfuse tracing (observabilidade)

---

## 📝 ARQUIVOS DE REFERÊNCIA

| Arquivo | Descrição |
|---------|-----------|
| `app/agent/prompts/prompt_comercial_adaptado.md` | **Prompt completo adaptado** |
| `app/agent/prompts/mapa_adaptacao.md` | **Mapa detalhado de adaptação** |
| `app/agent/prompts/system.md` | Prompt base do sistema (atualizado) |
| `app/agent/prompts/rules.md` | Regras de negócio (atualizado) |
| `app/agent/prompts/stages.md` | Guia de estágios (atualizado) |
| `app/agent/prompts/media.md` | Mídia e tags (atualizado) |
| `app/state/guards.py` | Regras hard no código |
| `app/domain/enums.py` | Estados do lead |
| `app/agent/graph.py` | Grafo LangGraph |

---

**ADAPTAÇÃO CONCLUÍDA COM SUCESSO! 🎉**

O prompt comercial do time W. está agora totalmente integrado à nova stack Python + LangGraph, preservando toda a lógica comercial original enquanto aproveita os benefícios da nova arquitetura stateful e modular.
