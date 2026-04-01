# 🔧 SOLUÇÃO DE PROBLEMAS - SDR AGENT

Guia para resolver erros comuns durante configuração e execução.

---

## ❌ ERRO: EOFError no generate_secrets.py

**Mensagem:**
```
EOFError: EOF when reading a line
```

**Causa:** Script sendo executado com redirecionamento de input (`<nul`)

**Solução:**

### Opção 1: Executar manualmente
```bash
.venv\Scripts\activate
python infra\scripts\generate_secrets.py
```

### Opção 2: Gerar via comando direto
```bash
python -c "import secrets; print('APP_SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('SESSION_SECRET=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('WEBHOOK_SECRET=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))" >> .env
```

### Opção 3: Copiar do output
O script mostra os segredos na tela. Copie manualmente para `.env`.

---

## ❌ ERRO: Permission denied no pip

**Mensagem:**
```
OSError: [Errno 13] Permission denied: 'c:\\users\\...\\pip\\cache\\...'
```

**Causa:** Permissões de arquivo ou pip com cache corrompido

**Solução:**

### Opção 1: Limpar cache do pip
```bash
python -m pip cache purge
python -m pip install --no-cache-dir -e .
```

### Opção 2: Usar --user
```bash
pip install --user -e .
```

### Opção 3: Executar como administrador
1. Feche terminal
2. Abra PowerShell como Administrador
3. Tente novamente

### Opção 4: Instalar pacotes individualmente
```bash
.venv\Scripts\activate

# Básicos
pip install fastapi uvicorn[standard] python-multipart jinja2

# Validação
pip install pydantic pydantic-settings python-dotenv

# HTTP
pip install httpx openai

# LangChain
pip install langchain langchain-core langchain-openai langgraph

# Banco
pip install supabase

# Observabilidade
pip install langfuse

# Testes
pip install pytest pytest-asyncio
```

---

## ❌ ERRO: Python version mismatch

**Mensagem:**
```
ERROR: Package 'xxx' requires Python >= 3.11 but you are using 3.x.x
```

**Causa:** Python desatualizado

**Solução:**

1. Verificar versão:
   ```bash
   python --version
   ```

2. Se for < 3.11, atualize:
   - Download: https://www.python.org/downloads/
   - Instale Python 3.11 ou 3.12
   - Recrie ambiente virtual:
     ```bash
     rmdir /s .venv
     python -m venv .venv
     ```

---

## ❌ ERRO: ModuleNotFoundError

**Mensagem:**
```
ModuleNotFoundError: No module named 'app'
```

**Causa:** Ambiente virtual não ativado ou pacote não instalado

**Solução:**

```bash
# Ativar ambiente virtual
.venv\Scripts\activate

# Instalar pacote em modo development
pip install -e .

# Ou instalar manualmente
pip install fastapi uvicorn pydantic supabase langgraph langfuse openai
```

---

## ❌ ERRO: OPENAI_API_KEY não configurada

**Mensagem:**
```
ValueError: OPENAI_API_KEY é obrigatória
```

**Causa:** Chave da OpenAI faltando no `.env`

**Solução:**

1. Obter chave em: https://platform.openai.com/api-keys
2. Editar `.env`:
   ```env
   OPENAI_API_KEY=sk-proj-...
   ```
3. Reiniciar API

---

## ❌ ERRO: SUPABASE_URL não configurada

**Mensagem:**
```
ValueError: SUPABASE_URL é obrigatória
```

**Causa:** Credenciais do Supabase faltando

**Solução:**

1. Acessar: https://app.supabase.com
2. Criar projeto
3. Ir em Project Settings → API
4. Copiar:
   - Project URL → `SUPABASE_URL`
   - service_role key → `SUPABASE_SERVICE_ROLE_KEY`
5. Editar `.env` com as chaves

---

## ❌ ERRO: relation "leads" does not exist

**Mensagem:**
```
psycopg2.errors.UndefinedTable: relation "leads" does not exist
```

**Causa:** Tabelas não criadas no Supabase

**Solução:**

1. Acessar Supabase → SQL Editor
2. Copiar conteúdo de `infra/sql/schema.sql`
3. Colar no SQL Editor
4. Executar (Run)
5. Verificar em Table Editor se tabelas foram criadas

---

## ❌ ERRO: Port already in use

**Mensagem:**
```
OSError: [WinError 10048] Only one usage of each socket address is permitted
```

**Causa:** Porta 8000 ou 8001 já está em uso

**Solução:**

### Opção 1: Matar processo
```bash
# Descobrir processo na porta 8000
netstat -ano | findstr :8000

# Matar processo (substitua PID pelo número encontrado)
taskkill /PID <PID> /F
```

### Opção 2: Mudar porta no .env
```env
# API
API_PORT=8002

# Playground
PLAYGROUND_PORT=8003
```

---

## ❌ ERRO: .env não existe

**Mensagem:**
```
FileNotFoundError: [Errno 2] No such file or directory: '.env'
```

**Causa:** Arquivo `.env` não foi criado

**Solução:**

```bash
# Copiar exemplo
copy .env.example .env

# Ou no PowerShell
Copy-Item .env.example .env
```

Depois edite `.env` e configure as chaves.

---

## ❌ ERRO: Segredos internos faltando

**Sintoma:** Aplicação inicia mas gera warnings sobre segredos

**Solução:**

### Gerar manualmente:
```bash
.venv\Scripts\activate

# Gerar e adicionar ao .env
echo APP_SECRET_KEY=%random%%random%%random% >> .env
echo SESSION_SECRET=%random%%random%%random% >> .env
echo WEBHOOK_SECRET=%random%%random%%random% >> .env
echo ENCRYPTION_KEY=%random%%random%%random% >> .env
```

### Ou usar Python:
```bash
python -c "import secrets; print('APP_SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('SESSION_SECRET=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('WEBHOOK_SECRET=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))" >> .env
```

---

## ❌ ERRO: Caracteres especiais no caminho

**Mensagem:**
```
UnicodeDecodeError: 'charmap' codec can't decode byte...
```

**Causa:** Caminho do projeto tem caracteres especiais

**Solução:**

1. Mover projeto para caminho sem espaços ou caracteres especiais:
   ```
   E:\sdr-agent\
   ```

2. Ou definir encoding no PowerShell:
   ```bash
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
   ```

---

## ❌ ERRO: Supabase connection failed

**Mensagem:**
```
supabase._async.client.SupabaseException: Connection refused
```

**Causa:** URL ou chave do Supabase incorretas

**Solução:**

1. Verificar se URL está correta (deve terminar em `.supabase.co`)
2. Verificar se está usando `service_role` key (não `anon` key)
3. Testar conexão no navegador:
   ```
   https://SEU_PROJETO.supabase.co/rest/v1/leads?select=*&limit=1
   ```
4. Verificar se schema.sql foi executado

---

## ❌ ERRO: OpenAI API error

**Mensagem:**
```
openai.AuthenticationError: Error code: 401
```

**Causa:** API Key da OpenAI inválida

**Solução:**

1. Verificar se chave começa com `sk-`
2. Testar chave no navegador:
   ```
   https://platform.openai.com/api-keys
   ```
3. Verificar se há crédito na conta
4. Gerar nova chave se necessário

---

## 🆘 AINDA COM PROBLEMAS?

### Debug mode

Ative log nível DEBUG no `.env`:
```env
LOG_LEVEL=DEBUG
```

### Verificar configurações

```bash
.venv\Scripts\activate
python -c "from app.config.settings import check_settings; check_settings()"
```

### Testar imports

```bash
python -c "
from app.config.settings import get_settings
from app.integrations.supabase.client import get_supabase_client
from app.integrations.openai.client import get_openai_client
print('✅ Todos imports OK')
"
```

### Logs completos

Os logs aparecem no terminal ao rodar API/Playground. Procure por:
- `ERROR` - Erros críticos
- `WARNING` - Avisos importantes
- `INFO` - Informações de inicialização

---

## 📞 SUPORTE ADICIONAL

Se nenhum destes resolver:

1. Verifique `CONFIGURACAO.md` para guia completo
2. Verifique `CHAVES_CONFIG.md` para lista de chaves
3. Re-executar `infra\scripts\configure.bat`
4. Reinstalar Python e recriar ambiente virtual

---

**FIM DO GUIA DE SOLUÇÃO DE PROBLEMAS**
