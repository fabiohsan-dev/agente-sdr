"""Node: generate_reply - Gera resposta do agente.

Otimizações aplicadas:
- Prompt seletivo: envia APENAS a etapa atual + próxima (~40% menos tokens)
- Classificação de intenção integrada: LLM retorna `intent` no output estruturado
- Deduplica conteúdo: não envia regras/exemplos já presentes nos prompts de etapa
"""

import json
import logging
import re
import time
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.agent.models.structured_outputs import AgentStructuredOutput
from app.config.settings import get_settings
from app.state.lead_states import AgentState

logger = logging.getLogger(__name__)

settings = get_settings()

# ============================================
# MAPEAMENTO ESTADO → ETAPAS RELEVANTES
# ============================================

_STATE_TO_STAGES = {
    "NEW": ["etapa_1"],
    "QUALIFYING": ["etapa_2"],
    "WAITING_PRIORITY_CONFIRMATION": ["etapa_2", "etapa_3"],
    "WAITING_FIT_CONFIRMATION": ["etapa_3", "etapa_4"],
    "WAITING_TIME": ["etapa_5"],
    "WAITING_EMAIL": ["etapa_5"],
    "BOOKING_IN_PROGRESS": ["etapa_5"],
    "SCHEDULED": ["etapa_6", "etapa_7", "pos_agendamento"],
    "POST_BOOKING_PENDING_MATERIALS": ["etapa_6"],
    "POST_BOOKING_PENDING_CHECKLIST": ["etapa_7"],
    "NO_MONEY": [],
    "CLOSED": [],
    "PAUSED_BY_HUMAN": [],
}


async def generate_reply(state: AgentState) -> AgentState:
    """
    Node de geração de resposta.

    Responsabilidades:
    - Carregar prompts modulares (seletivos por etapa)
    - Construir prompt completo com contexto
    - Chamar LLM com saída estruturada
    - Reconciliar intenção (keyword vs LLM)
    - Atualizar estado com decisão do agente
    """
    logger.debug("Iniciando geração de resposta")

    start_time = time.time()

    # ============================================
    # CARREGAR PROMPTS
    # ============================================

    prompts_dir = Path(__file__).parent.parent / "prompts"

    system_prompt = _load_prompt(prompts_dir / "system.md")
    rules_prompt = _load_prompt(prompts_dir / "rules.md")
    media_prompt = _load_prompt(prompts_dir / "media.md")

    # Carregar APENAS as etapas relevantes para o estado atual
    stages_prompt = _load_prompt(prompts_dir / "stages.md")
    selective_stages = _extract_relevant_stages(stages_prompt, state.current_state.value)

    # ============================================
    # CONSTRUIR PROMPT COMPLETO
    # ============================================

    full_prompt = _build_full_prompt(
        system_prompt=system_prompt,
        rules_prompt=rules_prompt,
        stages_prompt=selective_stages,
        media_prompt=media_prompt,
        state=state,
    )

    state.prompt_used = full_prompt
    logger.debug("Prompt construído: %d caracteres", len(full_prompt))

    # ============================================
    # CHAMAR LLM COM SAÍDA ESTRUTURADA
    # ============================================

    try:
        logger.info(f"Chamando LLM com modelo: {settings.openai_model}")
        logger.debug(f"Prompt tamanho: {len(full_prompt)} caracteres")

        # ============================================
        # LANGFUSE TRACING (se configurado)
        # ============================================
        from app.integrations.langfuse.tracing import get_langfuse

        langfuse = get_langfuse()
        langfuse_trace = None

        if langfuse.is_available():
            logger.info("🔵 Langfuse: tracing ativado")
            langfuse_trace = langfuse.trace(
                name="agent_generate_reply",
                user_id=str(state.lead_id) if state.lead_id else None,
                session_id=state.session_id,
                metadata={
                    "current_state": state.current_state.value,
                    "incoming_message": state.incoming_message[:100]
                    if state.incoming_message
                    else None,
                    "keyword_intent": state.metadata.get("intent", "UNKNOWN"),
                },
            )

        # ✅ Passar API Key explicitamente para evitar erro
        llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            timeout=settings.llm_timeout,
        ).with_structured_output(AgentStructuredOutput)

        logger.debug("Invocando LLM...")
        response: AgentStructuredOutput = await llm.ainvoke(
            [
                SystemMessage(
                    content="Você é um SDR experiente. Siga as regras e use o contexto fornecido."
                ),
                HumanMessage(content=full_prompt),
            ]
        )

        # Capturar geração no Langfuse
        if langfuse.is_available() and langfuse_trace:
            langfuse.generation(
                parent=langfuse_trace,
                name="llm_call",
                model=settings.openai_model,
                prompt=full_prompt[:5000],  # Limitar tamanho
                completion=response.reply_text,
                metadata={
                    "state_before": state.state_before.value if state.state_before else None,
                    "state_after": response.next_state,
                    "keyword_intent": state.metadata.get("intent", "UNKNOWN"),
                    "llm_intent": response.intent,
                    "actions": response.actions,
                },
            )
            logger.info("✅ Langfuse: geração capturada")

        logger.info(f"LLM retornou resposta: {len(response.reply_text)} caracteres")
        logger.info(f"Resposta LLM COMPLETA: {response.reply_text}")
        logger.debug(f"Resposta LLM (preview): {response.reply_text[:200]}...")

        # ============================================
        # RECONCILIAR INTENÇÃO (keyword vs LLM)
        # ============================================

        keyword_intent = state.metadata.get("intent", "UNKNOWN")
        llm_intent = response.intent

        # Intenções bloqueantes detectadas por keyword têm prioridade
        blocking_intents = {"NO_MONEY", "NOT_INTERESTED", "WANTS_PAUSE"}
        if keyword_intent in blocking_intents:
            final_intent = keyword_intent
            logger.info(
                f"🔒 Intent final: {keyword_intent} (keyword bloqueante, LLM disse {llm_intent})"
            )
        elif keyword_intent == "UNKNOWN" or keyword_intent == "RESPONDING_QUESTION":
            # Keyword não soube classificar bem — usar LLM
            final_intent = llm_intent
            logger.info(f"🤖 Intent final: {llm_intent} (LLM, keyword era {keyword_intent})")
        else:
            # Ambos classificaram — preferir LLM pois é mais preciso
            final_intent = llm_intent
            logger.info(
                f"🤖 Intent final: {llm_intent} (LLM preferido, keyword era {keyword_intent})"
            )

        state.metadata["intent"] = final_intent
        state.metadata["intent_keyword"] = keyword_intent
        state.metadata["intent_llm"] = llm_intent
        state.metadata["intent_source"] = "reconciled"

        # Atualizar flags se LLM detectou algo que keyword não pegou
        if final_intent == "NO_MONEY" and not state.no_money_flag:
            state.no_money_flag = True
            state.metadata["no_money_detected"] = True
            logger.info("🔴 NO_MONEY detectado pelo LLM (keyword não pegou)")

        if final_intent == "READY_TO_BOOK":
            state.metadata["ready_to_book"] = True

        # ============================================
        # ATUALIZAR ESTADO COM RESPOSTA
        # ============================================

        state.reply_text = response.reply_text

        # O LLM decide o next_state, mas o decide_stage já calculou o estado correto
        # como âncora. Se o LLM regredir para um estado anterior indevidamente, usamos
        # o estado do decide_stage para garantir o avanço correto do funil.
        llm_next_state = response.next_state
        decided_next_state = state.next_state  # calculado pelo decide_stage

        from app.domain.enums import LeadState

        state_order = [
            "NEW",
            "QUALIFYING",
            "WAITING_PRIORITY_CONFIRMATION",
            "WAITING_FIT_CONFIRMATION",
            "WAITING_TIME",
            "WAITING_EMAIL",
            "BOOKING_IN_PROGRESS",
            "SCHEDULED",
            "POST_BOOKING_PENDING_MATERIALS",
            "POST_BOOKING_PENDING_CHECKLIST",
        ]
        _terminal = {"NO_MONEY", "CLOSED", "PAUSED_BY_HUMAN"}

        # Se o LLM sugere um estado terminal, respeitar sempre
        if llm_next_state in _terminal:
            state.next_state = LeadState(llm_next_state)
        elif decided_next_state and llm_next_state:
            llm_order = state_order.index(llm_next_state) if llm_next_state in state_order else -1
            decided_order = (
                state_order.index(decided_next_state.value)
                if decided_next_state.value in state_order
                else -1
            )
            # Usar o mais avançado entre o que o LLM decidiu e o que o decide_stage calculou
            if llm_order >= decided_order:
                state.next_state = LeadState(llm_next_state)
            else:
                logger.info(
                    f"⚠️ LLM sugeriu regressão {decided_next_state.value} → {llm_next_state}. "
                    f"Mantendo {decided_next_state.value} (decide_stage)."
                )
                # mantém state.next_state = decided_next_state (já está setado)
        else:
            state.next_state = LeadState(llm_next_state) if llm_next_state else decided_next_state
        state.actions = response.actions
        state.should_schedule_follow = response.should_schedule_follow
        state.should_call_booking_tool = response.should_call_booking_tool
        state.should_send_materials = response.should_send_materials
        state.should_send_checklist = response.should_send_checklist
        state.should_pause_ai = response.should_pause_ai
        state.follow_reason = response.follow_reason

        # ============================================
        # PROCESSAR TAGS DE MÍDIA
        # ============================================

        # Extrair e processar tags de mídia da resposta
        from app.services.media_tag_service import (
            extract_media_tags,
            format_for_display,
        )

        # Extrair mídias mencionadas
        media_items = extract_media_tags(response.reply_text)
        if media_items:
            state.metadata["media_tags"] = media_items
            logger.debug(f"Tags de mídia encontradas: {media_items}")

        # Formatar para exibição (separar texto e mídia)
        formatted = format_for_display(response.reply_text)
        state.reply_text = formatted["text"]
        state.metadata["media"] = formatted["media"]

        # Calcular tokens (estimativa)
        state.tokens_used = _estimate_tokens(full_prompt, response.reply_text)

        logger.info(f"Resposta gerada: {len(state.reply_text)} chars, {len(media_items)} mídias")

    except Exception as e:
        logger.error(f"❌ ERRO CRÍTICO na geração de resposta: {type(e).__name__}: {e}")
        logger.error(f"Estado atual: {state.current_state}")
        logger.error(
            f"Mensagem: {state.incoming_message[:100] if state.incoming_message else 'None'}"
        )

        import traceback

        error_trace = traceback.format_exc()
        logger.error(f"Traceback:\n{error_trace}")

        state.error = f"{type(e).__name__}: {e}"
        state.reply_text = _get_fallback_response(state)
        state.next_state = state.current_state

    # Calcular latência
    state.latency_ms = int((time.time() - start_time) * 1000)
    state.model_used = settings.openai_model

    logger.debug(f"Resposta gerada em {state.latency_ms}ms")
    return state


def _load_prompt(path: Path) -> str:
    """Carrega prompt de arquivo e interpola variáveis dinâmicas de configuração."""
    try:
        content = path.read_text(encoding="utf-8")
        # Interpolar URLs dinâmicas do ambiente/settings
        if "{materials_drive_url}" in content:
            content = content.replace("{materials_drive_url}", settings.materials_drive_url)
        if "{case_study_url}" in content:
            content = content.replace("{case_study_url}", settings.case_study_url)
        if "{audio_padrao_url}" in content:
            audio_url = settings.audio_padrao_url or "https://cdn.exemplo.com/audio-padrao.m4a"
            content = content.replace("{audio_padrao_url}", audio_url)
        return content
    except FileNotFoundError:
        logger.warning(f"Prompt não encontrado: {path}")
        return ""


def _extract_relevant_stages(full_stages: str, current_state: str) -> str:
    """
    Extrai APENAS as seções de etapa relevantes para o estado atual.

    Economia estimada: ~3.900 tokens por chamada (envia 1-2 etapas em vez de 7).
    """
    stage_keys = _STATE_TO_STAGES.get(current_state, [])

    if not stage_keys:
        # Estado terminal — enviar apenas regras globais do stages.md
        return _extract_section(full_stages, "VISÃO GERAL") or ""

    # Mapeamento de chave → regex para encontrar a seção no markdown
    section_map = {
        "etapa_1": r"## ETAPA 1 —.*?(?=\n## ETAPA 2|---\s*\n## ETAPA 2|\Z)",
        "etapa_2": r"## ETAPA 2 —.*?(?=\n## ETAPA 3|---\s*\n## ETAPA 3|\Z)",
        "etapa_3": r"## ETAPA 3 —.*?(?=\n## ETAPA 4|---\s*\n## ETAPA 4|\Z)",
        "etapa_4": r"## ETAPA 4 —.*?(?=\n## ETAPA 5|---\s*\n## ETAPA 5|\Z)",
        "etapa_5": r"## ETAPA 5 —.*?(?=\n## ETAPA 6|---\s*\n## ETAPA 6|\Z)",
        "etapa_6": r"## ETAPA 6 —.*?(?=\n## ETAPA 7|---\s*\n## ETAPA 7|\Z)",
        "etapa_7": r"## ETAPA 7 —.*?(?=\n## MODO PÓS|---\s*\n## MODO PÓS|\Z)",
        "pos_agendamento": r"## MODO PÓS-AGENDAMENTO.*?(?=\n## RESUMO DE ESTADOS|---\s*\n## RESUMO|\Z)",
    }

    sections = []

    # Sempre incluir visão geral (compacta)
    visao = _extract_section(full_stages, "VISÃO GERAL")
    if visao:
        sections.append(visao.strip())

    # Extrair seções relevantes
    for key in stage_keys:
        pattern = section_map.get(key)
        if pattern:
            match = re.search(pattern, full_stages, re.DOTALL)
            if match:
                sections.append(match.group(0).strip())

    # Sempre incluir resumo de estados (compacto)
    resumo = re.search(r"## RESUMO DE ESTADOS.*", full_stages, re.DOTALL)
    if resumo:
        sections.append(resumo.group(0).strip())

    result = "\n\n---\n\n".join(sections)

    logger.debug(
        f"Prompt seletivo: {len(result)} chars para estado {current_state} "
        f"(original: {len(full_stages)} chars, economia: {len(full_stages) - len(result)} chars)"
    )

    return result


def _extract_section(text: str, heading: str) -> str | None:
    """Extrai uma seção pelo nome do heading."""
    pattern = rf"## {re.escape(heading)}.*?(?=\n## |\Z)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(0) if match else None


def _build_full_prompt(
    system_prompt: str,
    rules_prompt: str,
    stages_prompt: str,
    media_prompt: str,
    state: AgentState,
) -> str:
    """Constrói prompt completo com contexto."""

    # Contexto sistêmico
    system_context = json.dumps(state.system_context, indent=2, ensure_ascii=False)

    # Mensagem do usuário
    user_message = state.incoming_message or "[Sem mensagem de texto]"

    # Histórico recente
    conversation_history = state.conversation_context or "[Sem histórico]"

    # Intent do keyword classifier (para o LLM refinar)
    keyword_intent = state.metadata.get("intent", "UNKNOWN")

    # ============================================
    # GUARDRAIL AAB: Detectar pergunta e injetar instrução reforçada
    # ============================================
    aab_guardrail = ""
    has_question = (
        "?" in user_message
        or keyword_intent == "ASKING_SPECIFIC_QUESTION"
        or any(
            kw in user_message.lower()
            for kw in [
                "como funciona",
                "qual o valor",
                "quanto custa",
                "vocês atendem",
                "atendem esse",
                "qual o desafio",
                "como é feito",
                "o que é",
                "funciona como",
                "pode me explicar",
                "quero entender",
                "como vocês",
                "qual a diferença",
                "o que vocês fazem",
                "preço",
            ]
        )
    )

    if has_question:
        logger.info("🎯 AAB GUARDRAIL: Pergunta detectada na mensagem do lead")
        aab_guardrail = """
---

## ⚠️ ALERTA: PERGUNTA DETECTADA — PADRÃO AAB OBRIGATÓRIO

O lead fez uma PERGUNTA na mensagem. Você DEVE seguir o padrão AAB:

**A — ACKNOWLEDGE (Reconhecer):** Mostre que entendeu a pergunta
**A — ANSWER (Responder):** Responda de forma direta e confiante (1-2 frases)
**B — BRIDGE (Conectar):** Faça a ponte para o script com um conectivo natural

### EXEMPLO CONCRETO:
- Lead: "500. Como funciona isso?"
- NÃO FAÇA: "Faaaaala Jonathan..." + áudio (ignorou a pergunta!)
- FAÇA: "Boa pergunta! A gente faz captação ativa de clientes pra advogados usando um método validado. Inclusive, deixa eu te mandar um áudio rápido que explica direitinho como funciona na prática... Faaaaala Jonathan..." + áudio

### REGRA DE OURO:
Se o lead perguntou QUALQUER coisa, sua resposta DEVE começar respondendo a pergunta.
O script da etapa vem DEPOIS, conectado com "Inclusive...", "E por falar nisso...", "Aliás...", etc.
NUNCA ignore a pergunta do lead. Isso quebra rapport e escala a objeção.
"""

    prompt = f"""
{system_prompt}

---

{rules_prompt}

---

## ETAPAS RELEVANTES PARA O ESTADO ATUAL

{stages_prompt}

---

{media_prompt}

---

## CONTEXTO SISTÊMICO ATUAL

```json
{system_context}
```

---

## HISTÓRICO DA CONVERSA

{conversation_history}

---

## MENSAGEM DO USUÁRIO

{user_message}

---

## PRÉ-CLASSIFICAÇÃO DE INTENÇÃO

O sistema pré-classificou a intenção como: **{keyword_intent}**
(Você pode ajustar essa classificação no campo `intent` da sua resposta se discordar.)
{aab_guardrail}
---

## SUA TAREFA

Analise o contexto acima e responda com:
1. **reply_text**: Sua resposta para o usuário (natural, conversacional).
   - **IMPORTANTE**: Se o lead fez uma PERGUNTA na mensagem (sobre nicho, área, dúvida), aplique o padrão AAB:
     - Primeiro responda a pergunta brevemente (1-2 frases, com confiança)
     - Depois conecte naturalmente com o script da etapa atual usando um conectivo ("Inclusive...", "E por falar nisso...", "Aliás...")
     - O script da etapa SEMPRE deve ser entregue completo após a resposta consultiva
   - Se o lead NÃO fez uma pergunta, siga o script da etapa normalmente
2. **next_state**: Próximo estado do lead (baseado nas regras e estágio atual)
3. **actions**: Lista de ações a executar (ex: ["cancel_follow", "send_materials"])
4. **should_schedule_follow**: true/false - deve agendar follow-up?
5. **should_call_booking_tool**: true/false - deve oferecer agendamento?
6. **should_send_materials**: true/false - deve enviar materiais?
7. **should_send_checklist**: true/false - deve enviar checklist?
8. **should_pause_ai**: true/false - deve pausar a IA? Use APENAS quando:
   - (A) Lead recusa após tratamento de objeção ("não quero", "não tenho interesse" repetido)
   - (B) Lead não tem condições financeiras ("sem dinheiro", "preciso me planejar")
   - (C) Lead pede humano / demonstra resistência ao bot
   - (D) Lead encerrou elegantemente e não há mais o que fazer
   - NÃO usar para: dúvidas de preço, "vou pensar", "fica pra depois"
   - ORDEM: primeiro responda com elegância em reply_text, depois sinalize pause
9. **follow_reason**: Motivo do follow-up (se aplicável)
10. **intent**: Sua classificação da intenção do lead (refine a pré-classificação se necessário)

Responda em formato JSON estruturado.
"""

    return prompt


def _estimate_tokens(prompt: str, response: str) -> int:
    """Estima número de tokens (aproximado)."""
    # Aproximação: 1 token ≈ 3.1 caracteres em português
    return (len(prompt) + len(response)) // 3


def _get_fallback_response(state: AgentState) -> str:
    """Retorna resposta fallback em caso de erro."""
    if state.no_money_flag:
        return "Entendo perfeitamente. Agradeço sua transparência e ficamos à disposição quando a situação mudar!"
    elif state.current_state.value == "SCHEDULED":
        return "Sua reunião está agendada! Em breve enviarei os materiais de preparação."
    else:
        return "Obrigado pela mensagem! Deixe-me verificar as informações e já retorno."
