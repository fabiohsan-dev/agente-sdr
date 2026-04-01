# ⚡ COMEÇAR AGORA - SDR AGENT

Guia rápido de 5 minutos para começar a testar.

---

## 🎯 OBJETIVO

Ter o projeto rodando localmente em **5 minutos**.

---

## ✅ PRÉ-REQUISITOS

- [ ] Python 3.11+ instalado
- [ ] Conta na OpenAI (https://platform.openai.com)
- [ ] Conta no Supabase (https://app.supabase.com)

---

## 🚀 PASSO A PASSO RÁPIDO

### 1. Executar Configuração (1 minuto)

```bash
cd E:\Agente-w-py\sdr-agent-project
infra\scripts\configure.bat
```

Isso vai:
- ✅ Criar ambiente virtual
- ✅ Gerar segredos internos
- ✅ Instalar dependências básicas

---

### 2. Configurar Chaves (2 minutos)

Edite o arquivo `.env` e adicione:

```env
# OpenAI (obrigatório)
OPENAI_API_KEY=sk-proj-...

# Supabase (obrigatório)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
```

**Onde obter:**
- OpenAI: https://platform.openai.com/api-keys
- Supabase: https://app.supabase.com → Project Settings → API

---

### 3. Criar Banco no Supabase (1 minuto)

1. Acesse: https://app.supabase.com
2. Selecione seu projeto
3. Vá em **SQL Editor**
4. Copie conteúdo de `infra\sql\schema.sql`
5. Cole e execute (Run)

---

### 4. Rodar API (30 segundos)

```bash
infra\scripts\run_api.bat
```

Deve aparecer:
```
INFO: Uvicorn running on http://127.0.0.1:8000
```

---

### 5. Rodar Playground (30 segundos)

Em **outro terminal**:

```bash
infra\scripts\run_playground.bat
```

Deve aparecer:
```
INFO: Uvicorn running on http://127.0.0.1:8001
```

---

### 6. Testar (1 minuto)

1. Acesse: http://127.0.0.1:8001
2. Digite: `500`
3. Clique em **Enviar**

**Resposta esperada:**
```
Faaaaala, muito bom te ver por aqui!
\\
[MEDIA:AUDIO_PADRAO]
```

---

## ⚠️ SE ALGO DER ERRADO

### Erro no configure.bat?

Use o script alternativo:
```bash
infra\scripts\install.bat
```

### Erro de permissão?

Execute como Administrador ou:
```bash
pip install --user -e .
```

### Segredos não foram gerados?

Gere manualmente:
```bash
python -c "import secrets; print('APP_SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('SESSION_SECRET=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('WEBHOOK_SECRET=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))" >> .env
```

### Outras dúvidas?

Veja `TROUBLESHOOTING.md` para soluções detalhadas.

---

## 📋 CHECKLIST RÁPIDO

Antes de testar, marque:

- [ ] `.env` existe e tem `OPENAI_API_KEY`
- [ ] `.env` existe e tem `SUPABASE_URL`
- [ ] `.env` existe e tem `SUPABASE_SERVICE_ROLE_KEY`
- [ ] Segredos internos foram gerados (4 chaves)
- [ ] Schema.sql executado no Supabase
- [ ] API rodando (http://127.0.0.1:8000)
- [ ] Playground rodando (http://127.0.0.1:8001)

---

## 🎉 PRONTO!

Se tudo estiver OK, o projeto está rodando!

**Próximos passos:**
- Testar diferentes mensagens
- Testar com URLs de áudio/imagem
- Ver logs no terminal
- Explorar documentação

---

## 📚 DOCUMENTAÇÃO COMPLETA

| Arquivo | Para quê? |
|---------|-----------|
| `CONFIGURACAO.md` | Guia completo passo-a-passo |
| `CHAVES_CONFIG.md` | O que é automático vs manual |
| `TROUBLESHOOTING.md` | Solução de problemas |
| `README.md` | Visão geral do projeto |
| `ADAPTACAO_PROMPT.md` | Prompt comercial adaptado |

---

**TEMPO ESTIMADO: 5-10 minutos** ⏱️
