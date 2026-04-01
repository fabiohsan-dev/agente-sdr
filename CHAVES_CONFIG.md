# 🔑 CHAVES DE CONFIGURAÇÃO - SDR AGENT

Guia definitivo do que pode ser gerado automaticamente e do que precisa buscar manualmente.

---

## ✅ PODE SER GERADO AUTOMATICAMENTE

Estas chaves são **internas da aplicação** e podem/ devem ser geradas automaticamente.

### Script de Geração

```bash
# Método 1: Script interativo (recomendado)
python infra\scripts\generate_secrets.py

# Método 2: Comandos individuais
python -c "import secrets; print('APP_SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('SESSION_SECRET=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('WEBHOOK_SECRET=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
```

### Variáveis Auto-Geradas

| Variável | Tamanho | Uso | Onde é usada |
|----------|---------|-----|--------------|
| `APP_SECRET_KEY` | 32 bytes | Tokens internos, JWT | `app/config/settings.py` |
| `SESSION_SECRET` | 32 bytes | Sessões do playground | `apps/playground/server.py` |
| `WEBHOOK_SECRET` | 32 bytes | Webhooks futuros (Chatwoot) | `apps/api/routes/chatwoot.py` |
| `ENCRYPTION_KEY` | 32 bytes | Encriptação de dados | `app/services/encryption.py` |

### Quando São Geradas

- **Primeira execução:** `infra\scripts\configure.bat` gera automaticamente
- **Re-geração:** Execute `generate_secrets.py` manualmente
- **Validade:** Permanente (não expira)

### Importante

⚠️ **Se regenerar as chaves:**
- Sessões ativas serão invalidadas
- Tokens JWT anteriores não funcionarão mais
- Dados encriptados anteriores não poderão ser desencriptados

**Recomendação:** Gere uma vez e mantenha as mesmas chaves.

---

## 🔑 PRECISA BUSCAR MANUALMENTE (SERVIÇOS EXTERNOS)

Estas chaves são de **serviços de terceiros** e devem ser obtidas nos painéis correspondentes.

### Obrigatórias (Não funciona sem)

| Variável | Onde Obter | Passo a Passo |
|----------|------------|---------------|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys | 1. Login na OpenAI<br>2. Criar conta<br>3. Adicionar crédito<br>4. Criar API Key |
| `SUPABASE_URL` | https://app.supabase.com | 1. Login no Supabase<br>2. Criar projeto<br>3. Copiar URL em Project Settings |
| `SUPABASE_SERVICE_ROLE_KEY` | https://app.supabase.com/project/_/settings/api | 1. Ir em Project Settings<br>2. API<br>3. Copiar service_role key |

### Opcionais (Funciona sem, mas perde funcionalidade)

| Variável | Onde Obter | Perde se não tiver |
|----------|------------|-------------------|
| `CALCOM_API_KEY` | https://app.cal.com/settings/developer | Agendamento de reuniões |
| `CALCOM_EVENT_TYPE_ID` | https://app.cal.com/event-types | Agendamento de reuniões |
| `LANGFUSE_PUBLIC_KEY` | https://cloud.langfuse.com | Tracing e observabilidade |
| `LANGFUSE_SECRET_KEY` | https://cloud.langfuse.com | Tracing e observabilidade |

---

## 📋 RESUMO VISUAL

### Obrigatório ✅

```
┌─────────────────────────────────────────────────────────┐
│  OBRIGATÓRIO - Sem isso NÃO funciona                    │
├─────────────────────────────────────────────────────────┤
│  OPENAI_API_KEY           [Obter na OpenAI]             │
│  SUPABASE_URL             [Obter no Supabase]           │
│  SUPABASE_SERVICE_ROLE_KEY [Obter no Supabase]          │
└─────────────────────────────────────────────────────────┘
```

### Automático 🤖

```
┌─────────────────────────────────────────────────────────┐
│  AUTOMÁTICO - Gerado pelo script                        │
├─────────────────────────────────────────────────────────┤
│  APP_SECRET_KEY           [generate_secrets.py]         │
│  SESSION_SECRET           [generate_secrets.py]         │
│  WEBHOOK_SECRET           [generate_secrets.py]         │
│  ENCRYPTION_KEY           [generate_secrets.py]         │
└─────────────────────────────────────────────────────────┘
```

### Opcional ⚪

```
┌─────────────────────────────────────────────────────────┐
│  OPCIONAL - Funciona sem, mas perde features            │
├─────────────────────────────────────────────────────────┤
│  CALCOM_API_KEY           [Agendamento]                 │
│  CALCOM_EVENT_TYPE_ID     [Agendamento]                 │
│  LANGFUSE_PUBLIC_KEY      [Observabilidade]             │
│  LANGFUSE_SECRET_KEY      [Observabilidade]             │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 FLUXO RECOMENDADO

### 1. Primeira Configuração

```bash
# Passo 1: Executar configuração automática
infra\scripts\configure.bat

# Isso gera automaticamente:
# - APP_SECRET_KEY
# - SESSION_SECRET
# - WEBHOOK_SECRET
# - ENCRYPTION_KEY

# Passo 2: Editar .env manualmente
# Adicionar:
# - OPENAI_API_KEY
# - SUPABASE_URL
# - SUPABASE_SERVICE_ROLE_KEY
```

### 2. Verificar

```bash
# Ativar ambiente
.venv\Scripts\activate

# Verificar configuração
python -c "from app.config.settings import check_settings; check_settings()"
```

### 3. Testar

```bash
# Rodar API
infra\scripts\run_api.bat

# Em outro terminal, rodar Playground
infra\scripts\run_playground.bat
```

---

## 🔒 SEGURANÇA DAS CHAVES

### Chaves Internas (Auto-Geradas)

| Aspecto | Recomendação |
|---------|--------------|
| Armazenamento | Arquivo `.env` (já no .gitignore) |
| Compartilhamento | Nunca compartilhe |
| Rotação | Não é necessário rotacionar |
| Backup | Guarde cópia em local seguro |

### Chaves Externas (Serviços de Terceiros)

| Aspecto | Recomendação |
|---------|--------------|
| Armazenamento | `.env` para desenvolvimento |
| Produção | Use variáveis de ambiente do sistema |
| Compartilhamento | Nunca compartilhe |
| Rotação | Rotacione periodicamente (90 dias) |
| Monitoramento | Monitore uso no painel do serviço |

---

## 📝 EXEMPLO DE .ENV COMPLETO

```env
# ============================================
# OPENAI / LLM (OBRIGATÓRIO)
# ============================================
OPENAI_API_KEY=sk-proj-abc123def456...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7

# ============================================
# SUPABASE (OBRIGATÓRIO)
# ============================================
SUPABASE_URL=https://abc123xyz.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ============================================
# CAL.COM (OPCIONAL)
# ============================================
CALCOM_API_KEY=
CALCOM_BASE_URL=https://api.cal.com/v1
CALCOM_EVENT_TYPE_ID=

# ============================================
# LANGFUSE (OPCIONAL)
# ============================================
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com

# ============================================
# SEGURANÇA INTERNA (AUTO-GERADO)
# ============================================
APP_SECRET_KEY=x8vK2mN9pL4qR7sT1wX5yZ3bC6dF0gH
SESSION_SECRET=a2bC4dE6fG8hI0jK1lM3nO5pQ7rS9tU
WEBHOOK_SECRET=v1wX3yZ5aB7cD9eF1gH3iJ5kL7mN9oP
ENCRYPTION_KEY=q2rS4tU6vW8xY0zA1bC3dE5fG7hI9jK

# ============================================
# CDN / STORAGE
# ============================================
CDN_BASE_URL=

# ============================================
# APLICAÇÃO
# ============================================
APP_ENV=development
TIMEZONE=America/Sao_Paulo
LOG_LEVEL=INFO

# ============================================
# API SERVER
# ============================================
API_HOST=127.0.0.1
API_PORT=8000

# ============================================
# PLAYGROUND SERVER
# ============================================
PLAYGROUND_HOST=127.0.0.1
PLAYGROUND_PORT=8001

# ============================================
# LIMITES E TIMEOUTS
# ============================================
HTTP_TIMEOUT=30
LLM_TIMEOUT=60
MAX_HISTORY_MESSAGES=20

# ============================================
# REDIS (OPCIONAL)
# ============================================
REDIS_URL=
REDIS_TTL=3600

# ============================================
# RATE LIMITING
# ============================================
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60
```

---

## 🧪 VALIDAÇÃO

### Verificar se chaves internas foram geradas

```bash
python -c "
from app.config.settings import get_settings
s = get_settings()
print('APP_SECRET_KEY:', '✅' if s.app_secret_key else '❌')
print('SESSION_SECRET:', '✅' if s.session_secret else '❌')
print('WEBHOOK_SECRET:', '✅' if s.webhook_secret else '❌')
print('ENCRYPTION_KEY:', '✅' if s.encryption_key else '❌')
"
```

### Verificar se chaves externas estão configuradas

```bash
python -c "
from app.config.settings import get_settings
s = get_settings()
print('OPENAI_API_KEY:', '✅' if s.openai_api_key else '❌')
print('SUPABASE_URL:', '✅' if s.supabase_url else '❌')
print('SUPABASE_SERVICE_ROLE_KEY:', '✅' if s.supabase_service_role_key else '❌')
print('CALCOM_API_KEY:', '⚪' if s.calcom_enabled else '⚪ Não configurado')
print('LANGFUSE:', '⚪' if s.langfuse_enabled else '⚪ Não configurado')
"
```

---

## ❓ PERGUNTAS FREQUENTES

### Posso usar as mesmas chaves em produção?

**Internas (auto-geradas):** Sim, mas gere novas chaves específicas para produção.

**Externas:** Não! Use chaves diferentes para desenvolvimento e produção.

### O que acontece se eu perder as chaves internas?

- **Sessões:** Usuários serão deslogados
- **Tokens:** Tokens JWT anteriores não funcionarão
- **Dados encriptados:** Não poderão ser desencriptados

**Solução:** Tenha backup das chaves em local seguro.

### Preciso rotacionar as chaves?

**Internas:** Não é necessário, a menos que haja vazamento.

**Externas:** Sim, recomenda-se rotacionar a cada 90 dias.

### Posso compartilhar o arquivo .env?

**NUNCA!** O `.env` contém chaves sensíveis.

- ✅ Compartilhe `.env.example`
- ❌ Nunca compartilhe `.env`
- ✅ Use `.gitignore` (já configurado)

---

## 📞 SUPORTE

Se tiver problemas com configuração:

1. Veja `CONFIGURACAO.md` para guia passo-a-passo
2. Execute `check_settings()` para diagnosticar
3. Verifique logs da API e Playground

---

**FIM DO GUIA DE CHAVES**
