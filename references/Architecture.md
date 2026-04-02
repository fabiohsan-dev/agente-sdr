# Architecture.md

Este documento é a referência oficial de arquitetura do projeto **agente-w-sdr**. Quando houver conflito entre implementação atual, prompts ou decisões rápidas, **este documento prevalece**.

## 1. Objetivo

Migrar o projeto de um agente conduzido por prompt para uma aplicação **determinística, modular, auditável e segura para produção**.

## 2. Diagnóstico da base atual

A base atual já possui ativos importantes e **não deve ser reescrita do zero**.

### Reaproveitar
- `app/domain/enums.py`: estados e enums do domínio.
- `app/state/guards.py`: regras hard já codificadas.
- `app/agent/nodes/classify_intent.py`: classificador keyword-based, útil como primeira barreira determinística.
- `app/repositories/*.py`: camada de persistência já existente.
- `app/services/booking_service.py`: serviço de booking reaproveitável.
- `app/integrations/calcom/client.py`: cliente Cal.com é um ativo importante.
- `app/services/follow_up_service.py`: cadência fixa é válida.
- `app/agent/nodes/persist_decision.py`: snapshots e eventos são úteis.
- `infra/sql/schema.sql`: boa base, embora precise de migrações.

### Refatorar forte
- `app/state/lead_states.py`: hoje mistura input, estado, decisão, telemetria e side effects.
- `app/agent/graph.py`: pode continuar como orquestrador, mas não como lugar da lógica de negócio.
- `apps/api/routes/chat.py`: rota não deve conter criação oportunista de lead nem lógica central.
- `apps/api/routes/webhook.py`: deve virar intake assíncrono com dedupe e lock.

### Substituir no formato atual
- `app/agent/nodes/generate_reply.py`
- `app/agent/models/structured_outputs.py`
- `app/agent/nodes/maybe_call_tools.py`
- `app/agent/nodes/decide_stage.py`

## 3. Princípios obrigatórios

### 3.1 Thin Client, Fat Server
O LLM é apenas um componente de **interpretação** e **geração de linguagem**.  
O LLM **não** controla regra de negócio.

O LLM pode:
- classificar intenção quando heurística não bastar;
- extrair entidades textuais (email, horário, timezone, objeção, pedido de humano);
- gerar `reply_text` após a decisão do sistema.

O LLM não pode:
- decidir `next_state`;
- decidir `should_call_booking_tool`;
- decidir `should_schedule_follow`;
- decidir `should_pause_ai`;
- disparar side effects diretamente.

### 3.2 Isolamento de comportamento
Cada etapa do funil deve viver em módulo próprio. Alterações em qualificação não podem quebrar agendamento, follow-up ou envio de materiais.

### 3.3 State Machine determinística
O estado da conversa pertence ao back-end. Toda transição deve ser função de:
- estado atual persistido;
- sinal normalizado de entrada;
- fatos persistidos;
- políticas e guards explícitas.

### 3.4 Tool calling com trilho rígido
Ferramentas não são chamadas pelo LLM. Ferramentas são chamadas por **comandos tipados** emitidos pelo servidor.

### 3.5 Idempotência por padrão
Mensagens duplicadas, retries e webhooks concorrentes devem produzir um único efeito líquido.

## 4. Padrões adotados

Esta arquitetura segue padrões consolidados até agosto de 2025:
- Finite State Machine / State Pattern
- Thin Client, Fat Server
- Hexagonal / Ports and Adapters
- Inbox / Outbox
- Idempotent Consumer
- Saga / Process Manager
- Optimistic Concurrency + Lock por conversa
- Deterministic Core, Side-Effect Shell

## 5. Arquitetura alvo

```text
Clients/Canais
  Playground | Chatwoot | Instagram | Workers
        │
        ▼
Ingress Adapters
  validação + normalização + dedupe key
        │
        ▼
Intake Service / Inbox
  persiste evento inbound + idempotência + enqueue
        │
        ▼
Conversation Processor
  lock por conversa + load aggregate + state machine + action planner
        │
   ┌────┴─────────┐
   ▼              ▼
Response Builder  Action Executor
   │              │
   └────┬─────────┘
        ▼
Persistence + Audit + Outbox
```

## 6. Estrutura de pastas obrigatória

```text
apps/
  api/
    routes/
      chat.py
      webhook.py
      media.py
      health.py
      metrics.py

app/
  application/
    intake/
      service.py
      schemas.py
      dedupe.py
    orchestration/
      conversation_processor.py
      action_planner.py
      response_builder.py
      result_types.py
    behaviors/
      qualification/
        policy.py
        transitions.py
        response_contract.py
        prompts.md
        tests/
      scheduling/
        policy.py
        transitions.py
        command_factory.py
        response_contract.py
        prompts.md
        tests/
      materials/
        policy.py
        transitions.py
        response_contract.py
        tests/
      followup/
        policy.py
        transitions.py
        command_factory.py
        tests/
      handoff/
        policy.py
        transitions.py
        tests/
      closing/
        policy.py
        transitions.py
        tests/
    llm/
      intent_extractor.py
      response_generator.py
      schemas.py
    commands/
      booking.py
      followup.py
      materials.py
      handoff.py
    executors/
      booking_executor.py
      followup_executor.py
      materials_executor.py
      handoff_executor.py

  domain/
    lead/
      enums.py
      aggregate.py
      state_machine.py
      transitions.py
      signals.py
      invariants.py
      policies.py

  infrastructure/
    integrations/
    persistence/
      repositories/
    locks/
    queue/
    observability/

  workers/
    conversation_worker.py
    followup_worker.py
    outbox_worker.py

references/
  Architecture.md
```

### Regra de isolamento
Cada pasta em `application/behaviors/` deve conter sua própria policy, transições e testes. Nenhum comportamento pode importar a lógica interna do outro.

## 7. Modelo canônico de entrada

Toda entrada externa deve virar um `InboundEnvelope`:
- `source`
- `external_event_id`
- `dedupe_key`
- `received_at_utc`
- `session_key`
- `tenant_id`
- `contact_ref`
- `payload_kind`
- `text`
- `media_url`
- `media_metadata`
- `raw_payload`

## 8. State Machine oficial

### Estados oficiais
- `NEW`
- `QUALIFYING`
- `WAITING_PRIORITY_CONFIRMATION`
- `WAITING_FIT_CONFIRMATION`
- `WAITING_TIME`
- `WAITING_EMAIL`
- `BOOKING_IN_PROGRESS`
- `SCHEDULED`
- `POST_BOOKING_PENDING_MATERIALS`
- `POST_BOOKING_PENDING_CHECKLIST`
- `NO_MONEY`
- `CLOSED`
- `PAUSED_BY_HUMAN`

### Regra central
A state machine é a única autoridade sobre `state_after`.

Assinatura conceitual:

```text
transition(current_state, signal, facts) -> DecisionEnvelope
```

### Sinais normalizados
O sistema trabalha com sinais, não com improviso textual. Exemplos:
- `GREETING`
- `QUALIFICATION_ANSWER`
- `ASKING_SPECIFIC_QUESTION`
- `READY_TO_BOOK`
- `EMAIL_PROVIDED`
- `NO_MONEY`
- `NOT_INTERESTED`
- `WANTS_HUMAN`
- `MEDIA_RECEIVED`
- `BOOKING_CONFIRMED`
- `MATERIALS_SENT_CONFIRMED`
- `CHECKLIST_SENT_CONFIRMED`

### Transições-alvo
- `NEW -> QUALIFYING`
- `QUALIFYING -> WAITING_PRIORITY_CONFIRMATION`
- `WAITING_PRIORITY_CONFIRMATION -> WAITING_FIT_CONFIRMATION`
- `WAITING_FIT_CONFIRMATION -> WAITING_TIME`
- `WAITING_TIME -> WAITING_EMAIL`
- `WAITING_EMAIL -> BOOKING_IN_PROGRESS` apenas com email válido
- `BOOKING_IN_PROGRESS -> POST_BOOKING_PENDING_MATERIALS` apenas com booking confirmado
- `POST_BOOKING_PENDING_MATERIALS -> POST_BOOKING_PENDING_CHECKLIST` após envio de materiais
- `POST_BOOKING_PENDING_CHECKLIST -> SCHEDULED` após checklist enviado/confirmado
- `* -> NO_MONEY` quando o signal for `NO_MONEY`
- `* -> PAUSED_BY_HUMAN` com handoff humano
- `* -> CLOSED` com opt-out ou encerramento definitivo

### Transições proibidas
- `BOOKING_IN_PROGRESS -> SCHEDULED` sem confirmação real
- `SCHEDULED` voltar ao funil comercial
- `NO_MONEY` ser reativado automaticamente por prompt
- `PAUSED_BY_HUMAN` ser retomado automaticamente por prompt

## 9. Papel do LLM

### Permitido
#### Intent Extraction
Saída permitida:
- `intent`
- `confidence`
- `email_candidate`
- `timezone_candidate`
- `requested_slot_candidate`
- `objection_type`
- `asked_human`
- `contains_question`

#### Response Generation
Saída permitida:
- `reply_text`
- `optional_media_tags`

### Proibido
O LLM não pode devolver:
- `next_state`
- `should_schedule_follow`
- `should_call_booking_tool`
- `should_send_materials`
- `should_send_checklist`
- `should_pause_ai`

## 10. Trilho rígido de tool calling

Toda tool deve ser acionada por comando tipado.

### Contrato mínimo do comando
- `command_id`
- `command_type`
- `lead_id`
- `conversation_id`
- `tenant_id`
- `payload`
- `idempotency_key`
- `requested_at_utc`
- `causation_event_id`
- `correlation_id`

### Comandos oficiais iniciais
- `CreateBookingCommand`
- `CancelPendingFollowCommand`
- `ScheduleFollowCommand`
- `SendMaterialsCommand`
- `SendChecklistCommand`
- `PauseAICommand`
- `HandoffToHumanCommand`
- `SaveLeadEmailCommand`

### Pré-condições obrigatórias para booking
Só emitir `CreateBookingCommand` quando:
- estado atual permitir;
- email válido estiver confirmado;
- timezone estiver resolvido;
- horário estiver em UTC;
- horário não estiver no passado;
- slot pertencer à disponibilidade real;
- `lead_id` existir;
- houver `idempotency_key`.

### Resultado formal de tool
Toda execução deve devolver:
- `command_id`
- `status` (`success`, `noop`, `retryable_error`, `fatal_error`)
- `external_ref`
- `user_safe_message`
- `audit_payload`
- `executed_at_utc`

## 11. Idempotência e concorrência

### Inbox obrigatória
Deve existir uma tabela `inbox_events` com pelo menos:
- `source`
- `external_event_id`
- `dedupe_key`
- `session_key`
- `payload_hash`
- `status`
- `received_at`
- `processed_at`
- `raw_payload`

### Regra de dedupe
1. usar `source + external_event_id` quando existir;
2. senão usar `dedupe_key`;
3. senão usar hash do payload normalizado + janela temporal.

### Lock por conversa
Deve existir lock por `session_key` ou `conversation_id`. Apenas um processador por conversa por vez.

### Versionamento otimista
`leads` e `conversations` devem ganhar `version INTEGER NOT NULL DEFAULT 0`.

### Outbox
Toda saída para canal externo deve ser persistida em `outbox_messages` antes do envio real.

### Idempotência de side effects
Cada execução de tool deve ter chave única. Exemplos:
- booking: `lead_id + slot_start_utc + email`
- follow cancel: `lead_id + pending_follow_id + action_type`
- materials: `lead_id + template + conversation_id`

## 12. Alterações obrigatórias no banco

### Novas colunas
#### `leads`
- `version INTEGER NOT NULL DEFAULT 0`
- `tenant_id UUID NULL`
- `last_signal TEXT NULL`
- `last_transition_at TIMESTAMPTZ NULL`

#### `conversations`
- `version INTEGER NOT NULL DEFAULT 0`
- `tenant_id UUID NULL`
- `last_processed_inbox_event_id UUID NULL`

#### `messages`
- `source TEXT NULL`
- `external_message_id TEXT NULL`
- `dedupe_key TEXT NULL`

### Novas tabelas
- `inbox_events`
- `outbox_messages`
- `tool_executions`
- `conversation_locks` (se lock table for a estratégia adotada)

## 13. Fluxo oficial de processamento

### Webhook inbound
1. canal envia webhook;
2. rota autentica e normaliza;
3. `IntakeService` grava `inbox_events`;
4. se duplicado, retorna ack e encerra;
5. enfileira processamento;
6. worker adquire lock;
7. carrega aggregate;
8. normaliza signal;
9. roda state machine;
10. persiste transição + snapshots + eventos;
11. executa comandos;
12. gera resposta textual;
13. publica outbox;
14. outbox worker envia ao canal.

### Playground
Modo síncrono é aceitável apenas em desenvolvimento, mas deve usar as mesmas abstrações do pipeline oficial.

### Follow-up worker
1. busca `follow_jobs` vencidos;
2. adquire lock;
3. valida se o estado ainda permite follow;
4. monta `OutboundMessagePlan` fixo;
5. publica outbox;
6. conclui job;
7. agenda próximo step, se aplicável.

## 14. Contrato por comportamento

Cada comportamento deve expor, conceitualmente:

```text
BehaviorModule
- can_handle(state, signal) -> bool
- evaluate(state, signal, facts) -> BehaviorDecision
- build_response_plan(decision) -> ResponsePlan
- build_commands(decision) -> list[Command]
```

### Módulos obrigatórios
- `qualification/`
- `scheduling/`
- `materials/`
- `followup/`
- `handoff/`
- `closing/`

## 15. Regras obrigatórias de resposta

- geração textual acontece **depois** da decisão do sistema;
- deve haver fallback determinístico para `NO_MONEY`, `PAUSED_BY_HUMAN`, `CLOSED`, falha do LLM e lead já agendado;
- tags de mídia devem ser tratadas como parte do `OutboundMessagePlan`, não como side effect escondido no texto.

## 16. Observabilidade e auditoria

Registrar no mínimo:
- `inbox_event_received`
- `signal_normalized`
- `state_transitioned`
- `command_planned`
- `tool_executed`
- `outbox_published`
- `outbound_sent`
- `processing_failed`

`agent_snapshots` continua existindo, mas snapshot é observabilidade, não motor de negócio.

## 17. Estratégia de migração

### Fase 1 — Congelar contratos
- introduzir `InboundEnvelope`, `DecisionEnvelope`, `Command`, `ToolExecutionResult`.

### Fase 2 — Separar decisão do LLM
- trocar o output atual do LLM por dois schemas: intenção e geração textual;
- remover `next_state` e `should_*` do LLM.

### Fase 3 — Action planner/executor
- quebrar `maybe_call_tools.py` em executores por comando;
- adicionar idempotency key por tool.

### Fase 4 — Intake assíncrono
- criar `inbox_events`;
- webhook vira persist + enqueue + ack;
- criar lock por conversa.

### Fase 5 — Isolamento de comportamentos
- mover código para `application/behaviors/*`.

### Fase 6 — Outbox e workers
- introduzir `outbox_messages` e workers dedicados.

## 18. Critérios de aceite

A nova arquitetura só está implantada quando:
1. o LLM não decide estado oficial;
2. o LLM não decide tool calling oficial;
3. toda entrada passa por dedupe e inbox;
4. toda conversa é processada com lock;
5. todo side effect possui idempotency key;
6. booking só avança estado após confirmação real;
7. follow-up é determinístico;
8. cada comportamento possui módulo e testes próprios;
9. existe teste de concorrência para duplicidade;
10. existe trilha auditável ponta a ponta.

## 19. Mapeamento do legado para a arquitetura alvo

- `app/agent/graph.py` -> `application/orchestration/conversation_processor.py`
- `app/agent/nodes/classify_intent.py` -> `application/llm/intent_extractor.py` + `domain/lead/signals.py`
- `app/agent/nodes/decide_stage.py` -> `domain/lead/state_machine.py`
- `app/agent/nodes/maybe_call_tools.py` -> `application/orchestration/action_planner.py` + `application/executors/*`
- `app/agent/nodes/generate_reply.py` -> `application/orchestration/response_builder.py` + `application/llm/response_generator.py`
- `app/state/guards.py` -> `domain/lead/policies.py`
- `app/state/lead_states.py` -> `domain/lead/aggregate.py` + DTOs de aplicação
- `apps/api/routes/webhook.py` -> `application/intake/service.py` + worker

## 20. Decisões não negociáveis

1. o estado do lead pertence ao back-end;
2. o LLM não manda no funil;
3. toda tool é chamada por comando tipado;
4. toda entrada é deduplicada;
5. toda conversa é serializada por lock;
6. toda decisão relevante é auditável;
7. cada comportamento do SDR vive em módulo próprio;
8. regra de negócio nunca mora só em prompt.
