# 🚨 CORRIGINDO ERRO DE FALHA DO LLM

## PROBLEMA IDENTIFICADO

**Sintoma:**
- Latência de **1ms** (LLM não está sendo chamado)
- Resposta: "Obrigado pela mensagem! Deixe-me verificar..."
- Estado não muda (continua `NEW`)

**Causa:** LLM está falhando e caindo no `fallback_response`

---

## 🔍 DIAGNÓSTICO

### 1. Verificar Erros no Log

No terminal da API, procure por:
```
❌ ERRO CRÍTICO na geração de resposta: ...
```

### 2. Testar Conexão OpenAI

```bash
.venv\Scripts\activate
python infra\scripts\test_openai.py
```

**Saída esperada:**
```
✅ Conexão OK!
✅ Modelo 'gpt-4o-mini' disponível
✅ Geração OK!
```

---

## 🛠️ SOLUÇÕES

### Solução 1: Verificar Modelo OpenAI

**Problema:** "gpt-5.4-mini" **NÃO EXISTE**

**Modelos válidos:**
- ✅ `gpt-4o-mini` (recomendado)
- ✅ `gpt-4o`
- ✅ `gpt-4-turbo`
- ✅ `gpt-3.5-turbo`

**Como corrigir:**

No `.env`:
```env
OPENAI_MODEL=gpt-4o-mini
```

Ou no código (`app/config/settings.py`):
```python
openai_model: str = "gpt-4o-mini"
```

---

### Solução 2: Verificar API Key

**Problema:** API Key inválida ou expirada

**Como verificar:**
1. Acesse: https://platform.openai.com/api-keys
2. Verifique se chave existe
3. Verifique se há crédito na conta

**Como corrigir:**
```env
OPENAI_API_KEY=sk-proj-... (chave válida)
```

---

### Solução 3: Timeout Muito Curto

**Problema:** LLM demora mais que timeout configurado

**Como corrigir:**

No `.env`:
```env
LLM_TIMEOUT=120
```

No código (`app/config/settings.py`):
```python
llm_timeout: int = 120  # segundos
```

---

### Solução 4: Erro na Estrutura de Output

**Problema:** `with_structured_output()` falhando

**Como corrigir:**

Verificar se `pydantic` está instalado:
```bash
pip install pydantic pydantic-settings
```

---

## 🧪 TESTAR APÓS CORREÇÃO

### 1. Reiniciar API
```bash
# Fechar terminal atual
# Abrir novo terminal
infra\scripts\run_api.bat
```

### 2. Verificar Logs
Deve aparecer:
```
INFO | Chamando LLM com modelo: gpt-4o-mini
INFO | LLM retornou resposta: 150 caracteres
INFO | Resposta gerada e processada com sucesso
```

### 3. Testar no Playground
```
Enviar: 500
```

**Resposta esperada:**
```
Faaaaala [seu nome], muito bom te ver por aqui!

[Áudio]
https://sdr-w.agenciaalea.com.br/audio-w-padrao.m4a
```

---

## 📊 ERROS COMUNS

| Erro | Causa | Solução |
|------|-------|---------|
| `AuthenticationError` | API Key inválida | Gerar nova key |
| `TimeoutError` | Timeout curto | Aumentar `LLM_TIMEOUT` |
| `NotFoundError` | Modelo não existe | Usar `gpt-4o-mini` |
| `RateLimitError` | Sem crédito | Adicionar crédito |
| `ValidationError` | Output estruturado falhou | Reinstalar pydantic |

---

## 🔍 DEBUG PASSO A PASSO

### 1. Verificar Settings
```bash
python -c "
from app.config.settings import get_settings
s = get_settings()
print('Modelo:', s.openai_model)
print('API Key:', s.openai_api_key[:10] + '...')
print('Timeout:', s.llm_timeout)
"
```

### 2. Testar OpenAI Direto
```bash
python infra\scripts\test_openai.py
```

### 3. Verificar Logs da API
No terminal:
```
❌ ERRO CRÍTICO ...
```

Se aparecer erro, copiar e colar aqui para análise.

---

## ✅ CHECKLIST DE VALIDAÇÃO

- [ ] `.env` tem `OPENAI_API_KEY` válida
- [ ] `.env` tem `OPENAI_MODEL=gpt-4o-mini`
- [ ] `.env` tem `LLM_TIMEOUT=60` ou mais
- [ ] `test_openai.py` retorna ✅
- [ ] Logs mostram "Chamando LLM..."
- [ ] Logs mostram "LLM retornou resposta..."
- [ ] Playground retorna mensagem formatada

---

## 🆘 AINDA NÃO FUNCIONA?

### Coletar Informações

1. **Logs completos** da API
2. **Erro exato** mostrado
3. **Conteúdo do `.env`** (sem chaves reais)

### Enviar para Análise

Com essas informações, posso identificar o problema exato.

---

**FIM DO GUIA DE CORREÇÃO**
