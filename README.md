# SDR Agent — Agente Comercial Autônomo com LangGraph, FastAPI e Supabase

Agente SDR (*Sales Development Representative*) inteligente e determinístico, potencializado por **LangGraph (StateGraph)** para qualificação comercial de leads, agendamentos via **Cal.com**, persistência de snapshots no **Supabase (PostgreSQL)** e operação omnichannel via **Chatwoot** e **Playground Web**.

---

## 🎯 Visão Geral e Diferenciais

Diferente de chatbots estocásticos e fluxos frágeis, este Agente SDR opera com uma **Máquina de Estados Finitos (FSM)** estruturada para:

- **Qualificação Consultiva em 7 Etapas:** Avalia dor, nicho, faturamento, urgência, fit e disponibilidade de horário.
- **Otimização de Custos e Latência:** Prompts seletivos e modulares por etapa (~40% de economia de tokens) e pré-classificação heurística de intenções.
- **Auditoria e Compliance:** Gravação de snapshots (`agent_snapshots`) antes e depois de cada decisão com rastreio de tokens, latência e modelo.
- **Human-in-the-Loop:** Pausa automática do agente quando assumido por atendente humano (`PAUSED_BY_HUMAN`) e bloqueio de agendamento fora do perfil (`NO_MONEY`).
- **Suporte Multimodal:** Processamento de mensagens de texto, áudios com transcrição e imagens com análise.
- **Dashboard em Tempo Real:** Painel com métricas de conversão de funil, leads ativos e gráficos temporais via Chart.js.

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                       FRONT-ENDS                            │
│ ┌──────────────────────┐           ┌──────────────────────┐ │
│ │  Chatwoot Inbox      │           │ Playground Web       │ │
│ │  (WhatsApp/Insta)    │           │ Localhost:8001       │ │
│ └──────────┬───────────┘           └──────────┬───────────┘ │
└────────────┼──────────────────────────────────┼─────────────┘
             │ Webhook                          │ HTTP REST
             ▼                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      API FastAPI                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐  │
│  │ /webhook/       │ │ /metrics/       │ │ /chat         │  │
│  │ chatwoot        │ │ dashboard       │ │ (REST API)    │  │
│  └─────────────────┘ └─────────────────┘ └───────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LANGGRAPH AGENT                          │
│                                                             │
│  [ ingest ] ─→ [ load ] ─→ [ rules ] ─→ [ media ]           │
│                                              │              │
│  [ persist ] ←─ [ generate ] ←─ [ tools ] ←─ [ classify ]   │
│       │                                      │              │
│       ▼                                      ▼              │
│  [ finalize ] ─→ END                   [ decide ]           │
└─────────────────────────────┬───────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │   Supabase   │  │    Cal.com   │  │   Langfuse   │
    │ (PostgreSQL) │  │  (Agendador) │  │ (Telemetry)  │
    └──────────────┘  └──────────────┘  └──────────────┘
```

---

## 💻 Como Rodar Localmente

### 1. Pré-requisitos
- **Python 3.11+**
- Projeto no **Supabase** (com `schema.sql` executado)
- Chave de API da **OpenAI**

### 2. Instalação

```bash
# Clonar o repositório
git clone https://github.com/fabiohsan-dev/agente-w-sdr.git
cd agente-w-sdr

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# Instalar dependências
pip install -e ".[dev]"
```

### 3. Configurar `.env`

Copie o arquivo de exemplo e preencha as configurações:
```bash
cp .env.example .env
```

Configurações mínimas necessárias:
```env
# OPENAI (Obrigatório)
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini

# SUPABASE (Obrigatório)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# MATERIAIS E CASES (Opcional / Dinâmico)
MATERIALS_DRIVE_URL=https://drive.google.com/drive/folders/seu-link-de-cases
CASE_STUDY_URL=https://seusite.com/cases
```

### 4. Inicializar o Banco de Dados
No painel do Supabase, abra o **SQL Editor** e execute:
- `infra/sql/schema.sql` (cria tabelas, enums e triggers)
- `infra/sql/multi_tenancy.sql` (opcional: suporte multi-empresa)

### 5. Executar os Servidores

Abra dois terminais:

**Terminal 1 — API do Agente:**
```bash
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — Playground Web:**
```bash
uvicorn apps.playground.server:app --host 127.0.0.1 --port 8001 --reload
```

- **Playground Interativo:** [http://127.0.0.1:8001](http://127.0.0.1:8001)
- **Dashboard de Métricas:** [http://127.0.0.1:8000/metrics/dashboard](http://127.0.0.1:8000/metrics/dashboard)
- **Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🚀 Deploy em Produção (Docker + Traefik)

O projeto inclui configuração pronta para deploy com Docker Compose e suporte a proxy reverso com Traefik e cache em Redis.

```bash
# Subir containers em background
docker compose up -d --build

# Acompanhar logs da API
docker compose logs -f api
```

---

## 🛠️ Integração Omnichannel (Chatwoot)

1. No painel do **Chatwoot**, acesse **Configurações → Integrações → Webhooks**.
2. Adicione o endpoint do seu servidor:
   ```text
   https://sdr.seudominio.com/webhook/chatwoot
   ```
3. Selecione o evento `message_created`.
4. Configure as variáveis no seu `.env`:
   ```env
   CHATWOOT_BASE_URL=https://app.chatwoot.com
   CHATWOOT_API_TOKEN=seu_access_token
   CHATWOOT_ACCOUNT_ID=1
   CHATWOOT_INBOX_ID=1
   CHATWOOT_WEBHOOK_SECRET=seu_webhook_secret
   ```

---

## 🧪 Testes e Qualidade de Código

O repositório inclui suíte de testes unitários e padronização com **Ruff**:

```bash
# Executar testes unitários
pytest tests/ -v

# Verificar lint
ruff check app/ apps/

# Verificar formatação
ruff format --check app/ apps/
```

---

## 📦 Stack Tecnológica

- **Core & AI:** LangGraph, LangChain, OpenAI (GPT-4o / Structured Outputs)
- **Framework Web:** FastAPI, Uvicorn (uvloop), Jinja2
- **Banco de Dados:** Supabase (PostgreSQL 15+)
- **Observabilidade:** Langfuse, Chart.js Dashboard
- **Infraestrutura:** Docker, Docker Compose, Redis, Traefik

---

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais detalhes.
