# SDR Agent — Integração Chatwoot & Supabase

Agente SDR (Sales Development Representative) inteligente potencializado pelo **LangGraph** e desenhado para qualificação de leads, agendamentos via **Cal.com** e operação nativa integrada ao **Chatwoot** como Caixa de Entrada.

## 🎯 Visão Geral e Objetivo

Diferente de fluxos rígidos guiados por bots tradicionais, este Agente opera como um vendedor consultivo utilizando grafos conversacionais (LangGraph) para:
- **Qualificar Leads Dinamicamente:** Avalia urgência, budget, fit, prioridade e tempo de forma flexível.
- **Gerenciar Estado Comercial:** Gerencia com precisão as etapas de qualificação (do primeiro contato até o fechamento ou rejeição).
- **Integração Real-time com Chatwoot:** Atua como um operador invisível respondendo caixas de entrada de Instagram, WhatsApp e Web do Chatwoot de maneira autônoma através de Webhooks.
- **Agendamento Ativo:** Conecta com a API (V1) do Cal.com para garantir reunião caso a qualificação do lead seja sucesso.
- **Transparência Total (Dashboard):** Um painel de acompanhamento de funil e conversão operando no servidor.

---

## 🏗️ Arquitetura Moderna

```
┌─────────────────────────────────────────────────────────────┐
│                       FRONT-ENDS                            │
│ ┌──────────────────────┐           ┌──────────────────────┐ │
│ │  Chatwoot Inbox      │           │ Playground / Dev     │ │
│ │  (Insta, Wapp, Web)  │           │ Localhost:8001       │ │
│ └──────────┬───────────┘           └──────────┬───────────┘ │
└────────────┼──────────────────────────────────┼─────────────┘
             │ WebSocket/Webhook                │ HTTP
             ▼                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      API FastAPI                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐  │
│  │ /webhook/       │ │ /metrics/       │ │ /chat         │  │
│  │ chatwoot/message│ │ dashboard       │ │ (Dev API)     │  │
│  └─────────────────┘ └─────────────────┘ └───────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LANGGRAPH AGENT                          │
│                                                             │
│  [ ingest ] ─→ [ load ] ─→ [ rules ] ─→ [ classify ]        │
│                                              │              │
│  [ persist ] ←─ [ generate ] ←─ [ tools ] ←─ [ decide ]     │
└─────────────────────────────┬───────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │   Supabase   │  │    Cal.com   │  │   Langfuse   │
    │   (Banco)    │  │  (Agenda)    │  │  (Tracing)   │
    └──────────────┘  └──────────────┘  └──────────────┘
```

---

## 🚀 Como Fazer Deploy na VPS (Docker + Traefik)

O projeto possui uma infraestrutura 100% conteinerizada, desenhada para ser orquestrada com Docker Compose e exposta seguramente por um [Traefik](https://traefik.io/) Proxy reverso pré-existente.

### 1. Requisitos na Máquina Alvo
- Docker e Docker Compose instalados.
- Traefik configurado criando a network `traefik`.
- Um subdomínio garantido (Exemplo: `sdr.meudominio.com`).
- Conta e Supabase rodando (projeto criado via Painel da Supabase).

### 2. Configurações Prévias

Clone o repositório na sua VPS:
```bash
git clone https://github.com/fabiohsan-dev/agente-w-sdr.git
cd agente-w-sdr
```

Crie o arquivo de variáveis de ambiente:
```bash
cp .env.example .env
```

Configure pelo menos as obrigatoriedades do seu **`.env`**:
```env
# URL E CHAVE DO SUPABASE (Obrigatório)
SUPABASE_URL=https://<seu-projeto>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# DOMÍNIO DO TRAEFIK (Obrigatório para rotas HTTPs)
SDR_DOMAIN=sdr.meudominio.com

# TOKENS DE SEGURANÇA CHATWOOT (Obrigatório para Webhook)
CHATWOOT_URL=https://chat.seu-dominio.com
CHATWOOT_WEBHOOK_SECRET=token-secreto
CHATWOOT_WEBHOOK_URL_SUFFIX=/webhook/chatwoot/message

# OPENAI E CAL.COM (Obrigatórios ao Sistema Base)
OPENAI_API_KEY=sk-proj...
CALCOM_API_KEY=cal_live_xxxx...
CALCOM_EVENT_TYPE_ID=1234
```

### 3. Build & Subida (Up)

```bash
# Sobe a API e o Redis interno atrelados à rede Traefik externa.
docker compose up -d --build
```

A partir daqui a sua API de Inteligência já subirá atrelada ao domínio definido (com SSL via Traefik).

---

## 🛠 Integração Fácil com Chatwoot

A rota oficial do Webhook não expõe seu Agente livremente. Existe uma camada de validação baseada nos tokens seguros estipulados no `.env`.

1. Vá ao **Chatwoot** > Configurações > Integrações > **Webhooks**.
2. Adicione a URL base do seu servidor rodando via docker: 
   👉 `https://sdr.meudominio.com/webhook/chatwoot/message`
3. Assegure-se de marcar para escutar os eventos `message_created` (Obrigatório pelo menos).
4. O bot irá varrer automagicamente e apenas interceptar mensagens geradas "no lado do cliente" ou respostas originadas pelo usuário.

> Quando uma mensagem chega do lead, o Agente carrega o histórico do *Supabase* (se existir), computa grafos, altera etapas de lead, toma ações de agendamento (via *Cal.com*) e devolve ao *Chatwoot* postando em texto para o lead.

---

## 📊 Dashboard de Gerenciamento e Métricas

Uma grande vantagem dessa arquitetura é o **painel gerencial e analítico próprio** renderizado em tempo real pelas rotas da API em HTML e CSS unificado. 

Ele processa e mapeia os seguintes estados base do seu banco Supabase ativamente e atualiza de 30 em 30 segundos!

Basta acessar no seu navegador: `https://sdr.meudominio.com/metrics/dashboard`

![Dashboard Visual](https://img.icons8.com/color/48/000000/dashboard-layout.png)
*(No lado do desenvolvedor você não precisa se conectar ao Supabase para validar a adoção comercial de sua IA, basta acompanhar este atalho).*

---

## 💻 Desenvolvimento Local & Playground (Windows)

Se for desenvolver de maneira local, você não precisará do Chatwoot no primeiro instante, nós disponibilizamos um emulador de web (Playground). 

1. Tenha o *Python 3.11+* Instalado.
2. Na raiz:
   ```cmd
   infra\scripts\configure.bat
   ```
3. Preencha seu arquivo `.env`.
4. Abra dois painéis de terminal para rodar o emulador:
   ```cmd
   # Terminal 1 - A API do Agent principal
   infra\scripts\run_api.bat

   # Terminal 2 - Front-end de Emulação
   infra\scripts\run_playground.bat
   ```
5. Logue em `http://localhost:8001` no browser para debugar respostas do Bot de texto sem atrapalhar sua caixa de mensagem oficial na internet!

---

## 🚀 CI / CD (Pipeline de Produção)

Trabalhamos duro para suportar **GitHub Actions** mantendo tudo polido via padronizações modernas em Python (Linter **Ruff**). 
Para validar o projeto a longo-prazo durante melhorias pontuais ou commit em massa, rodamos no seu projeto checkings e builds automatizados de imagem:
```bash
# Validar erros de lintagem antes de dar commit
ruff check . --fix
```

A cada push para o repositório principal do GitHub, imagens Docker otimizadas podem ser construídas ou disponibilizadas pelo registry do Git e CI Actions sem atrito e sem esquecer caches sujos na VPS!

---

## 📦 Dependências Principais

- **FastAPI / Uvicorn (uvloop)** - Performance assíncrona web.
- **LangGraph & Langchain** - Motor cognitivo de etapas controladas.
- **Supabase** - Postgres R/W isolado.
- **Ruff / Pytest** - Formatação e Qualidade em Python Moderno.
- **Docker Compose** - Empacotamento Multi-Stage.

---
📝 **License**: MIT
