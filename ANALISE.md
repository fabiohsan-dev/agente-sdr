# 🔍 ANÁLISE DO PROJETO - SDR AGENT

Análise técnica das correções e melhorias implementadas.

---

## 🐛 PROBLEMAS IDENTIFICADOS

### 1. Formato da Mensagem Não Seguido

**Problema:**
O agente não estava enviando mensagens no formato correto:
```
Faaaaala [nome], muito bom te ver por aqui!

[Áudio]
Audio link
```

**Causa:**
- Prompt não era explícito o suficiente sobre o formato
- Tags de mídia não eram processadas
- Separador `\\` não era convertido

**Solução Implementada:**

#### a) Serviço de Processamento de Mídia
Criado `app/services/media_tag_service.py`:
- Processa tags `[MEDIA:AUDIO_PADRAO]` e `[MEDIA:CASE_GENERICO]`
- Converte `\\` em quebras de linha
- Extrai URLs das mídias
- Formata para exibição no frontend

#### b) Atualização do Node `generate_reply`
- Agora processa tags de mídia automaticamente
- Extrai mídias para metadata
- Formata resposta para exibição

#### c) Prompts Atualizados
- `system.md`: Instruções explícitas de formato
- `stages.md`: Scripts exatos para copiar
- Exemplos claros de uso de tags

---

### 2. Modelo OpenAI Incorreto

**Problema:**
Configuração mencionava "GPT 5.4-mini" (não existe)

**Solução:**
Modelos válidos:
- `gpt-4o-mini` ✅ (recomendado, custo-benefício)
- `gpt-4o` ✅ (mais inteligente, mais caro)
- `gpt-4-turbo` ✅
- `gpt-3.5-turbo` ✅ (mais barato, menos inteligente)

**Como configurar no `.env`:**
```env
OPENAI_MODEL=gpt-4o-mini
```

---

### 3. Tags de Mídia Não Apareciam

**Problema:**
Tags como `[MEDIA:AUDIO_PADRAO]` não eram exibidas corretamente

**Solução:**

#### Backend (`media_tag_service.py`):
```python
MEDIA_URLS = {
    "AUDIO_PADRAO": "https://sdr-w.agenciaalea.com.br/audio-w-padrao.m4a",
    "CASE_GENERICO": "https://sdr-w.agenciaalea.com.br/case-sergio.png",
}
```

#### Processamento:
1. LLM gera resposta com tag: `[MEDIA:AUDIO_PADRAO]`
2. Serviço extrai tag e converte para URL real
3. Frontend recebe URL completa para exibição

---

## 📊 FLUXO ATUALIZADO

### Envio de Mensagem (Etapa 1)

```
1. Usuário envia "500"
   ↓
2. LangGraph processa (nodes 1-7)
   ↓
3. generate_reply node:
   - Carrega prompts
   - Chama LLM (gpt-4o-mini)
   - LLM retorna:
     "Faaaaala João, muito bom te ver por aqui!
      \\
      [MEDIA:AUDIO_PADRAO]"
   ↓
4. media_tag_service processa:
   - Extrai tag [MEDIA:AUDIO_PADRAO]
   - Converte \\ para \n\n
   - Retorna URL: https://sdr-w.agenciaalea.com.br/audio-w-padrao.m4a
   ↓
5. Frontend recebe:
   {
     "reply": "Faaaaala João, muito bom te ver por aqui!\n\n\n\n**Ouvir áudio:** https://sdr-w.agenciaalea.com.br/audio-w-padrao.m4a",
     "media_tags": [
       {
         "tag": "[MEDIA:AUDIO_PADRAO]",
         "type": "audio",
         "url": "https://sdr-w.agenciaalea.com.br/audio-w-padrao.m4a"
       }
     ]
   }
   ↓
6. Playground exibe:
   - Texto: "Faaaaala João, muito bom te ver por aqui!"
   - Player de áudio com URL
```

---

## 🔧 ARQUIVOS MODIFICADOS

| Arquivo | Mudança |
|---------|---------|
| `app/services/media_tag_service.py` | **Novo** - Processa tags de mídia |
| `app/agent/nodes/generate_reply.py` | **Atualizado** - Processa tags |
| `app/agent/prompts/system.md` | **Atualizado** - Formato explícito |
| `app/agent/prompts/stages.md` | **Atualizado** - Scripts exatos |
| `app/config/settings.py` | **Atualizado** - Validação de modelo |

---

## ✅ TESTES RECOMENDADOS

### Teste 1: Etapa 1 (Saudação com Áudio)

```bash
# No playground, envie:
500
```

**Resposta esperada:**
```
Faaaaala [seu nome], muito bom te ver por aqui!

[Áudio]
https://sdr-w.agenciaalea.com.br/audio-w-padrao.m4a
```

### Teste 2: Verificar Tags no Log

No terminal da API, procure por:
```
DEBUG | Tags de mídia encontradas: [{'tag': '[MEDIA:AUDIO_PADRAO]', 'type': 'audio', ...}]
```

### Teste 3: Verificar Metadata

No response do chat, deve ter:
```json
{
  "metadata": {
    "media_tags": [
      {
        "tag": "[MEDIA:AUDIO_PADRAO]",
        "url": "https://sdr-w.agenciaalea.com.br/audio-w-padrao.m4a"
      }
    ]
  }
}
```

---

## 🎯 CONFIGURAÇÃO DO MODELO

### Modelos Disponíveis

| Modelo | Velocidade | Inteligência | Custo | Recomendado |
|--------|------------|--------------|-------|-------------|
| `gpt-4o-mini` | ⚡⚡⚡ | ⭐⭐⭐ | $ | ✅ Sim |
| `gpt-4o` | ⚡⚡ | ⭐⭐⭐⭐⭐ | $$$ | Uso avançado |
| `gpt-4-turbo` | ⚡⚡ | ⭐⭐⭐⭐ | $$ | Alternativa |
| `gpt-3.5-turbo` | ⚡⚡⚡ | ⭐⭐ | $ | Testes |

### Como Mudar Modelo

No `.env`:
```env
OPENAI_MODEL=gpt-4o-mini
```

Ou via código:
```python
settings.openai_model = "gpt-4o"
```

---

## 📝 EXEMPLO DE RESPOSTA FORMATADA

### Entrada do LLM
```
Faaaaala João, muito bom te ver por aqui!
\\
[MEDIA:AUDIO_PADRAO]
```

### Saída Processada
```python
{
  "reply_text": "Faaaaala João, muito bom te ver por aqui!\n\n\n\n**Ouvir áudio:** https://sdr-w.agenciaalea.com.br/audio-w-padrao.m4a",
  "media_tags": [
    {
      "tag": "[MEDIA:AUDIO_PADRAO]",
      "type": "audio",
      "url": "https://sdr-w.agenciaalea.com.br/audio-w-padrao.m4a",
      "name": "AUDIO_PADRAO"
    }
  ]
}
```

### Exibição no Frontend
```
Faaaaala João, muito bom te ver por aqui!

────────────────────────────
🔊 Áudio
https://sdr-w.agenciaalea.com.br/audio-w-padrao.m4a
────────────────────────────
```

---

## 🚀 PRÓXIMOS PASSOS

### 1. Testar Formato
```bash
# Reiniciar API
infra\scripts\run_api.bat

# No playground
http://127.0.0.1:8001
Enviar: 500
```

### 2. Verificar Logs
```
DEBUG | Tags de mídia encontradas: [...]
INFO | Resposta gerada e processada com sucesso
```

### 3. Ajustar Frontend (se necessário)

Se o playground não estiver exibindo corretamente:

**Opção A:** Atualizar `app.js` para detectar URLs de mídia
**Opção B:** Usar metadata `media_tags` para exibir player

---

## 📊 MÉTRICAS DE VALIDAÇÃO

| Métrica | Esperado | Como Verificar |
|---------|----------|----------------|
| Tags processadas | ✅ | Logs DEBUG |
| URL do áudio | ✅ | Response metadata |
| Separador `\\` convertido | ✅ | Texto formatado |
| Modelo correto | ✅ | `settings.openai_model` |

---

**FIM DA ANÁLISE TÉCNICA**
