# 🚀 GUIA DE CONFIGURAÇÃO - SDR AGENT

Guia completo para configurar o projeto para teste local no Windows.

---

## 📋 RESUMO RÁPIDO

### O que pode ser gerado automaticamente ✅
| Variável | Como gerar |
|----------|------------|
| `APP_SECRET_KEY` | `python infra/scripts/generate_secrets.py` |
| `SESSION_SECRET` | `python infra/scripts/generate_secrets.py` |
| `WEBHOOK_SECRET` | `python infra/scripts/generate_secrets.py` |
| `ENCRYPTION_KEY` | `python infra/scripts/generate_secrets.py` |

### O que você precisa buscar manualmente 🔑
| Variável | Onde obter | Obrigatório |
|----------|------------|-------------|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys | ✅ Sim |
| `SUPABASE_URL` | https://app.supabase.com | ✅ Sim |
| `SUPABASE_SERVICE_ROLE_KEY` | https://app.supabase.com/project/_/settings/api | ✅ Sim |
| `CALCOM_API_KEY` | https://app.cal.com/settings/developer | ⚪ Opcional |
| `CALCOM_EVENT_TYPE_ID` | https://app.cal.com | ⚪ Opcional |
| `LANGFUSE_PUBLIC_KEY` | https://cloud.langfuse.com | ⚪ Opcional |
| `LANGFUSE_SECRET_KEY` | https://cloud.langfuse.com | ⚪ Opcional |

---

## 📝 PASSO A PASSO

### PASSO 1: Verificar Pré-requisitos

**Python 3.11+**
```bash
python --version
```

Se não tiver Python instalado:
- Download: https://www.python.org/downloads/
- Marque: "Add Python to PATH" durante instalação

---

### PASSO 2: Executar Configuração Inicial

```bash
cd E:\Agente-w-py\sdr-agent-project

# Executar script de configuração
infra\scripts\configure.bat
```

Este script vai:
1. ✅ Verificar Python
2. ✅ Criar ambiente virtual (.venv)
3. ✅ Copiar .env.example para .env
4. ✅ Gerar segredos internos automaticamente
5. ✅ Instalar dependências
6. ✅ Verificar configurações

---

### PASSO 3: Configurar OpenAI API Key 🔑

1. Acesse: https://platform.openai.com/api-keys
2. Faça login ou crie conta
3. Clique em "Create new secret key"
4. Dê um nome (ex: "SDR Agent")
5. Copie a chave (começa com `sk-`)
6. Cole no arquivo `.env`:

```env
OPENAI_API_KEY=sk-proj-...
```

**Importante:**
- A chave é sensível a maiúsculas/minúsculas
- Não compartilhe ou coloque no Git
- Guarde em local seguro

---

### PASSO 4: Configurar Supabase 🔑

#### 4.1 Criar Projeto

1. Acesse: https://app.supabase.com
2. Clique em "New Project"
3. Preencha:
   - Name: `sdr-agent`
   - Database Password: (guarde em local seguro)
   - Region: Escolha a mais próxima (US East ou Europe)
4. Aguarde criação (2-3 minutos)

#### 4.2 Obter Credenciais

1. **URL do Projeto:**
   - Vá em: Project Settings → API
   - Copie "Project URL"
   - Cole no `.env`:
   ```env
   SUPABASE_URL=https://xxxxx.supabase.co
   ```

2. **Service Role Key:**
   - Vá em: Project Settings → API
   - Em "Project API keys", copie "service_role" (⚠️ NÃO use "anon")
   - Cole no `.env`:
   ```env
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
   ```

#### 4.3 Criar Tabelas no Banco

1. Acesse: https://app.supabase.com
2. Selecione seu projeto
3. Vá em: **SQL Editor** (ícone de terminal no menu lateral)
4. Clique em: **New Query**
5. Abra o arquivo: `infra/sql/schema.sql`
6. Copie TODO o conteúdo
7. Cole no SQL Editor do Supabase
8. Clique em: **Run** (ou Ctrl+Enter)
9. Aguarde: "Success. No rows returned"

**Verificar tabelas criadas:**
1. Vá em: **Table Editor** (ícone de tabela)
2. Deve ver 8 tabelas:
   - leads
   - conversations
   - messages
   - events
   - follow_jobs
   - bookings
   - media_assets
   - agent_snapshots

---

### PASSO 5: Configurar Cal.com (Opcional) 🔑

Se for usar agendamento nesta fase:

1. Acesse: https://app.cal.com
2. Faça login ou crie conta
3. Vá em: **Settings** → **Developer**
4. Em "API Keys", clique em "Create API Key"
5. Copie a chave
6. Cole no `.env`:
   ```env
   CALCOM_API_KEY=calcom_...
   ```

7. **Obter Event Type ID:**
   - Vá em: **Event Types**
   - Clique no evento que quer usar (ou crie um novo)
   - A URL será: `https://app.cal.com/event-types/123456`
   - O número final é o ID: `123456`
   - Cole no `.env`:
   ```env
   CALCOM_EVENT_TYPE_ID=123456
   ```

**Se NÃO for usar Cal.com:**
```env
CALCOM_API_KEY=
CALCOM_EVENT_TYPE_ID=
```

---

### PASSO 6: Configurar Langfuse (Opcional) 🔑

Se for usar observabilidade/tracing:

1. Acesse: https://cloud.langfuse.com
2. Faça login ou crie conta
3. Vá em: **Settings** → **API Keys**
4. Copie as chaves:
   ```env
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   ```

**Se NÃO for usar Langfuse:**
```env
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
```

---

### PASSO 7: Verificar Configuração

```bash
# Ativar ambiente virtual
.venv\Scripts\activate

# Verificar se tudo está configurado
python -c "from app.config.settings import check_settings; check_settings()"
```

**Saída esperada:**
```
============================================================
STATUS DAS CONFIGURAÇÕES
============================================================

SERVIÇOS EXTERNOS:
  ✅ OpenAI: Configurado
  ✅ Supabase: Configurado
  ⚪ Cal.com: Não configurado (opcional)
  ⚪ Langfuse: Não configurado (opcional)

============================================================
```

Se alguma chave obrigatória estiver faltando:
```
⚠️  CHAVES OBRIGATÓRIAS FALTANDO:
    - OPENAI_API_KEY
    - SUPABASE_URL
    - SUPABASE_SERVICE_ROLE_KEY
```

---

### PASSO 8: Rodar o Projeto

Abra **DOIS terminais**:

#### Terminal 1 - API
```bash
cd E:\Agente-w-py\sdr-agent-project
infra\scripts\run_api.bat
```

**Saída esperada:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     SDR Agent API iniciando em 127.0.0.1:8000
```

Acesse: http://127.0.0.1:8000/docs

#### Terminal 2 - Playground
```bash
cd E:\Agente-w-py\sdr-agent-project
infra\scripts\run_playground.bat
```

**Saída esperada:**
```
INFO:     Uvicorn running on http://127.0.0.1:8001
INFO:     SDR Agent Playground iniciando em 127.0.0.1:8001
```

Acesse: http://127.0.0.1:8001

---

## 🧪 TESTANDO NO PLAYGROUND

1. Acesse: http://127.0.0.1:8001
2. Preencha (opcional):
   - Nome: `João Silva`
   - Email: `joao@email.com`
3. Selecione: **Texto**
4. Digite: `500` (gatilho de entrada)
5. Clique em: **Enviar**

**Resposta esperada:**
```
Faaaaala João Silva, muito bom te ver por aqui!
\\
[MEDIA:AUDIO_PADRAO]
```

**Estado deve mudar para:** `QUALIFYING`

---

## 🔒 SEGURANÇA

### Segredos Gerados Automaticamente

O script `generate_secrets.py` gera:

| Variável | Uso |
|----------|-----|
| `APP_SECRET_KEY` | Tokens internos, JWT |
| `SESSION_SECRET` | Sessões do playground |
| `WEBHOOK_SECRET` | Webhooks futuros (Chatwoot) |
| `ENCRYPTION_KEY` | Encriptação de dados sensíveis |

**Estes segredos:**
- ✅ São gerados localmente
- ✅ São únicos para sua instalação
- ✅ Não precisam de painéis externos
- ✅ Devem ser mantidos em segredo

### Segredos de Serviços Externos

| Variável | Sensibilidade |
|----------|---------------|
| `OPENAI_API_KEY` | 🔴 Alta (pode gerar custos) |
| `SUPABASE_SERVICE_ROLE_KEY` | 🔴 Alta (acesso total ao banco) |
| `CALCOM_API_KEY` | 🟡 Média |
| `LANGFUSE_*` | 🟢 Baixa (apenas logging) |

**Proteja suas chaves:**
- ❌ NUNCA coloque no Git
- ❌ NUNCA compartilhe
- ✅ Use `.gitignore` (já configurado)
- ✅ Guarde em cofre de senhas

---

## 🐛 SOLUÇÃO DE PROBLEMAS

### Erro: "OPENAI_API_KEY não configurada"

**Causa:** Chave da OpenAI faltando ou inválida

**Solução:**
1. Verifique se `.env` existe
2. Confira se `OPENAI_API_KEY=` tem valor
3. Teste a chave: https://platform.openai.com/api-keys
4. Reinicie a API

---

### Erro: "SUPABASE_URL não configurada"

**Causa:** Credenciais do Supabase faltando

**Solução:**
1. Acesse: https://app.supabase.com
2. Copie URL e Service Role Key
3. Cole no `.env`
4. Execute schema.sql no SQL Editor

---

### Erro: "relation 'leads' does not exist"

**Causa:** Tabelas não criadas no Supabase

**Solução:**
1. Acesse Supabase → SQL Editor
2. Execute `infra/sql/schema.sql`
3. Verifique em Table Editor se tabelas existem

---

### Erro: "ModuleNotFoundError: No module named 'app'"

**Causa:** Ambiente virtual não ativado ou pacote não instalado

**Solução:**
```bash
# Ativar ambiente virtual
.venv\Scripts\activate

# Reinstalar pacote
pip install -e .
```

---

### Erro: "Port 8000 already in use"

**Causa:** API já está rodando

**Solução:**
1. Feche o terminal da API
2. Ou use outra porta no `.env`:
   ```env
   API_PORT=8002
   ```

---

### Playground não carrega

**Causa:** Servidor não está rodando

**Solução:**
1. Execute: `infra\scripts\run_playground.bat`
2. Acesse: http://127.0.0.1:8001
3. Verifique se não há erro no terminal

---

## 📞 SUPORTE

### Documentação
- README.md: Visão geral do projeto
- ENTREGA.md: Detalhes da implementação
- ADAPTACAO_PROMPT.md: Adaptação do prompt comercial

### Arquivos de Configuração
- `.env.example`: Template de variáveis
- `app/config/settings.py`: Validação de settings
- `infra/scripts/configure.bat`: Setup automático

### Logs e Debug
```bash
# Ver logs em tempo real
# (já saem no terminal ao rodar API/Playground)

# Nível de log no .env
LOG_LEVEL=DEBUG  # Mais detalhado
LOG_LEVEL=INFO   # Padrão
LOG_LEVEL=ERROR  # Apenas erros
```

---

## ✅ CHECKLIST FINAL

Antes de testar, verifique:

- [ ] Python 3.11+ instalado
- [ ] Ambiente virtual criado (.venv)
- [ ] Dependências instaladas
- [ ] `.env` configurado com:
  - [ ] `OPENAI_API_KEY` (obrigatório)
  - [ ] `SUPABASE_URL` (obrigatório)
  - [ ] `SUPABASE_SERVICE_ROLE_KEY` (obrigatório)
  - [ ] Segredos internos gerados (automático)
- [ ] Schema.sql executado no Supabase
- [ ] Tabelas criadas (8 tabelas)
- [ ] API rodando (http://127.0.0.1:8000)
- [ ] Playground rodando (http://127.0.0.1:8001)

**Se tudo estiver OK, o projeto está pronto para teste!** 🎉

---

## 🔄 ATUALIZAÇÃO DE SEGREDO

Para regenerar segredos internos:

```bash
# Método 1: Script interativo
python infra\scripts\generate_secrets.py

# Método 2: Comando rápido
python -c "import secrets; print('APP_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

---

**FIM DO GUIA DE CONFIGURAÇÃO**
