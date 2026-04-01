# SDR Agent

Agente SDR (Sales Development Representative) com LangGraph, FastAPI e Supabase para qualificação de leads e agendamento de reuniões.

## 🎯 Objetivo

Construir um agente SDR local que:
- Qualifica leads de forma consultiva
- Gerencia estados do lead (NEW, QUALIFYING, SCHEDULED, etc.)
- Agenda reuniões via Cal.com
- Processa mídia (áudio e imagem) via CDN
- Mantém rastreabilidade completa com Langfuse

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    PLAYGROUND (HTML/JS)                      │
│                    http://localhost:8001                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API FastAPI                             │
│                    http://localhost:8000                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  /chat      │  │  /media     │  │  /health    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LANGGRAPH AGENT                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │  ingest  │→│  load    │→│  rules   │→│  classify│        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │  decide  │→│  tools   │→│  generate│→│  persist │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │   Supabase   │  │    Cal.com   │  │   Langfuse   │
    │   (Banco)    │  │  (Agenda)    │  │  (Tracing)   │
    └──────────────┘  └──────────────┘  └──────────────┘
```

## 📁 Estrutura do Projeto

```
sdr-agent-project/
├── apps/
│   ├── api/                    # API FastAPI
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── chat.py         # Endpoint de chat
│   │   │   ├── media.py        # Endpoint de mídia
│   │   │   └── health.py       # Health check
│   │   └── deps.py
│   │
│   └── playground/             # Playground Web
│       ├── server.py
│       ├── templates/
│       │   └── chat.html
│       └── static/
│           ├── app.js
│           └── styles.css
│
├── app/
│   ├── config/                 # Configurações
│   │   ├── settings.py
│   │   └── logging.py
│   │
│   ├── domain/                 # Modelos de domínio
│   │   ├── lead.py
│   │   ├── conversation.py
│   │   ├── booking.py
│   │   └── enums.py
│   │
│   ├── state/                  # Estados e guards
│   │   ├── lead_states.py
│   │   ├── guards.py
│   │   ├── transitions.py
│   │   └── snapshots.py
│   │
│   ├── agent/                  # Agente LangGraph
│   │   ├── graph.py
│   │   ├── nodes/
│   │   │   ├── ingest_message.py
│   │   │   ├── load_state.py
│   │   │   ├── apply_hard_rules.py
│   │   │   ├── classify_intent.py
│   │   │   ├── decide_stage.py
│   │   │   ├── maybe_process_media.py
│   │   │   ├── maybe_call_tools.py
│   │   │   ├── generate_reply.py
│   │   │   ├── persist_decision.py
│   │   │   └── finalize.py
│   │   ├── prompts/
│   │   │   ├── system.md
│   │   │   ├── rules.md
│   │   │   ├── media.md
│   │   │   └── stages.md
│   │   └── models/
│   │       └── structured_outputs.py
│   │
│   ├── services/               # Serviços
│   │   ├── inbound_service.py
│   │   ├── outbound_service.py
│   │   ├── booking_service.py
│   │   ├── follow_up_service.py
│   │   ├── media_download_service.py
│   │   ├── audio_processing_service.py
│   │   ├── image_processing_service.py
│   │   └── context_service.py
│   │
│   ├── integrations/           # Integrações externas
│   │   ├── supabase/
│   │   ├── calcom/
│   │   ├── langfuse/
│   │   └── openai/
│   │
│   ├── repositories/           # Repositórios (banco)
│   │   ├── leads_repository.py
│   │   ├── conversations_repository.py
│   │   ├── messages_repository.py
│   │   ├── bookings_repository.py
│   │   ├── follow_jobs_repository.py
│   │   ├── media_assets_repository.py
│   │   └── agent_snapshots_repository.py
│   │
│   ├── schemas/                # Schemas Pydantic
│   │   ├── chat.py
│   │   ├── leads.py
│   │   ├── bookings.py
│   │   └── media.py
│   │
│   └── utils/                  # Utilitários
│       ├── datetime.py
│       ├── text.py
│       └── ids.py
│
├── infra/
│   ├── sql/
│   │   ├── schema.sql          # Schema do Supabase
│   │   └── migrations/
│   └── scripts/
│       ├── setup.bat           # Setup Windows
│       ├── run_api.bat         # Rodar API
│       └── run_playground.bat  # Rodar Playground
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .env.example
├── pyproject.toml
└── README.md
```

## 🚀 Quick Start (Windows)

### 1. Pré-requisitos

- Python 3.11+
- Conta no Supabase (gratuito)
- API Key da OpenAI
- (Opcional) Cal.com para agendamento
- (Opcional) Langfuse para observabilidade

### 2. Configuração Automática

```bash
# Navegue até a pasta do projeto
cd sdr-agent-project

# Execute configuração automática
infra\scripts\configure.bat
```

Este script vai:
- ✅ Criar ambiente virtual
- ✅ Copiar `.env.example` para `.env`
- ✅ Gerar segredos internos automaticamente
- ✅ Instalar dependências
- ✅ Verificar configurações

### 3. Configurar Chaves Externas

Edite o arquivo `.env` e configure:

```env
# OpenAI (OBRIGATÓRIO)
# Obter em: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-...

# Supabase (OBRIGATÓRIO)
# Obter em: https://app.supabase.com
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Cal.com (OPCIONAL)
CALCOM_API_KEY=
CALCOM_EVENT_TYPE_ID=

# Langfuse (OPCIONAL)
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
```

### 4. Criar Banco no Supabase

1. Acesse https://app.supabase.com
2. Crie um novo projeto
3. Vá para **SQL Editor**
4. Copie e execute o conteúdo de `infra/sql/schema.sql`

### 5. Verificar Configuração

```bash
# Ativar ambiente virtual
.venv\Scripts\activate

# Verificar configurações
python -c "from app.config.settings import check_settings; check_settings()"
```

### 6. Rodar o Projeto

Abra **dois terminais**:

**Terminal 1 - API:**
```bash
infra\scripts\run_api.bat
```
API rodará em http://127.0.0.1:8000

**Terminal 2 - Playground:**
```bash
infra\scripts\run_playground.bat
```
Playground rodará em http://127.0.0.1:8001

### 7. Testar

1. Acesse http://127.0.0.1:8001
2. Digite uma mensagem (ex: `500`)
3. Veja a resposta do agente
4. Teste com URLs de áudio/imagem

📖 **Guia completo:** Veja `CONFIGURACAO.md` para instruções detalhadas.

## 📊 Estados do Lead

| Estado | Descrição |
|--------|-----------|
| `NEW` | Lead novo, início da qualificação |
| `QUALIFYING` | Em qualificação ativa |
| `WAITING_PRIORITY_CONFIRMATION` | Aguardando confirmação de prioridade |
| `WAITING_FIT_CONFIRMATION` | Aguardando confirmação de fit |
| `WAITING_TIME` | Aguardando confirmação de tempo |
| `WAITING_EMAIL` | Aguardando email para agendamento |
| `BOOKING_IN_PROGRESS` | Processo de agendamento em andamento |
| `SCHEDULED` | Já agendado |
| `POST_BOOKING_PENDING_MATERIALS` | Aguardando envio de materiais |
| `POST_BOOKING_PENDING_CHECKLIST` | Aguardando envio de checklist |
| `NO_MONEY` | Lead disse que não tem condições |
| `CLOSED` | Lead fechado/finalizado |
| `PAUSED_BY_HUMAN` | Pausado por humano (handoff) |

## 🔧 Regras Hard de Negócio

Implementadas no código (não só no prompt):

1. **NO_MONEY**: Não oferece agendamento, não faz follow, encerra com elegância
2. **PAUSED_BY_HUMAN**: Agente não responde
3. **SCHEDULED**: Não reinicia roteiro comercial
4. **Lead respondeu**: Cancela follow pendente
5. **Booking confirmado**: Muda para `POST_BOOKING_PENDING_MATERIALS`
6. **Materiais enviados**: Muda para `POST_BOOKING_PENDING_CHECKLIST`

## 🎪 Testando no Playground

### Texto
1. Selecione "Texto"
2. Digite sua mensagem
3. Clique em "Enviar"

### Áudio (URL CDN)
1. Selecione "Áudio (URL)"
2. Cole a URL do arquivo de áudio (ex: https://cdn.ex.com/audio.mp3)
3. Opcional: adicione transcrição no metadata
4. Clique em "Enviar"

### Imagem (URL CDN)
1. Selecione "Imagem (URL)"
2. Cole a URL da imagem (ex: https://cdn.ex.com/image.png)
3. Opcional: adicione análise no metadata
4. Clique em "Enviar"

## 📝 API Endpoints

### POST /chat/
Envia mensagem para o agente.

```json
{
  "session_id": "sess_abc123",
  "message": "Olá, quero saber mais",
  "message_type": "text",
  "lead_email": "teste@email.com",
  "lead_name": "João"
}
```

### POST /chat/text
Chat simplificado de texto.

### POST /chat/media
Chat com mídia.

```json
{
  "session_id": "sess_abc123",
  "media_url": "https://cdn.ex.com/audio.mp3",
  "media_type": "audio",
  "transcription": "transcrição do áudio",
  "lead_email": "teste@email.com"
}
```

### POST /media/process
Processa arquivo de mídia (transcrição/análise).

## 🔌 Integrações Futuras (Chatwoot)

Esta fase **não usa Chatwoot**, mas a arquitetura está preparada:

1. **Webhook endpoint**: Criar rota para receber webhooks do Chatwoot
2. **Chatwoot client**: Implementar cliente para API do Chatwoot
3. **Message mapping**: Mapear mensagens Chatwoot ↔ formato interno
4. **Handoff**: Implementar handoff agent ↔ human via owner_mode

Pontos de extensão:
- `app/integrations/chatwoot/` (nova pasta)
- `app/agent/nodes/maybe_call_tools.py` (adicionar chatwoot tool)
- `apps/api/routes/chatwoot_webhook.py` (nova rota)

## 🧪 Testes

```bash
# Rodar testes
pytest

# Com coverage
pytest --cov=app --cov-report=html
```

## 📦 Dependências

- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **langgraph** - Runtime do agente
- **langchain** - Framework LLM
- **langfuse** - Observabilidade
- **supabase** - Banco de dados
- **pydantic** - Validação
- **httpx** - HTTP client
- **jinja2** - Templates

## 🚧 Em Implementação

- [ ] Processamento real de áudio (Whisper)
- [ ] Processamento real de imagem (GPT-4 Vision)
- [ ] Integração completa com Cal.com
- [ ] Follow-up agendado (cron/scheduler)
- [ ] Envio de materiais/checklist
- [ ] Tests unitários e e2e

## 📄 License

MIT
