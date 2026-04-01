"""Node: classify_intent - Classifica intenção via keywords (sem LLM).

Otimização: substituímos a chamada LLM (~700 tokens, 1-3s) por pattern matching
determinístico. A classificação fina é feita pelo LLM no generate_reply
via campo `intent` na saída estruturada.
"""

import logging
import re

from app.state.lead_states import AgentState

logger = logging.getLogger(__name__)


# ============================================
# PADRÕES DE INTENÇÃO (regex, case-insensitive)
# ============================================

_NO_MONEY_PATTERNS = re.compile(
    r"(n[ãa]o\s+tenh?o\s+(condi[çc][oõ]es|dinheiro|grana|verba|caixa|or[çc]amento))"
    r"|(sem\s+(dinheiro|grana|condi[çc][oõ]es|or[çc]amento|caixa))"
    r"|(preciso\s+me\s+planejar\s+financ)"
    r"|(est[áa]\s+apertado)"
    r"|(t[áa]\s+apertado)"
    r"|(fora\s+do\s+or[çc]amento)"
    r"|(n[ãa]o\s+posso\s+(investir|pagar|gastar))",
    re.IGNORECASE,
)

_NOT_INTERESTED_PATTERNS = re.compile(
    r"^(n[ãa]o\s+quero|n[ãa]o\s+tenho\s+interesse|n[ãa]o\s+obrigado|para\s+de|"
    r"desinscrever|cancelar|sair|n[ãa]o\s+preciso|sem\s+interesse|"
    r"bloqueado|spam|chega|parar|me\s+tira)$"
    r"|^n[ãa]o$",
    re.IGNORECASE,
)

_GREETING_PATTERNS = re.compile(
    r"^(oi|ol[áa]|e\s*a[ií]|fala|salve|bom\s*dia|boa\s*tarde|boa\s*noite"
    r"|hey|hello|hi|tudo\s*bem|blz|beleza|faaaala|opa)[\s!?.]*$",
    re.IGNORECASE,
)

_READY_TO_BOOK_PATTERNS = re.compile(
    r"(pode\s+marcar|vamos\s+l[áa]|pode\s+agendar|quero\s+agendar|bora\s+marcar"
    r"|marca\s+a[ií]|pode\s+ser|agendar|marcar\s+reuni[ãa]o|vamos\s+agendar)",
    re.IGNORECASE,
)

_QUESTION_PATTERNS = re.compile(
    r"(\?)"  # Tem interrogação
    r"|(voc[eê]s\s+atendem)"
    r"|(funciona\s+pra)"
    r"|(como\s+funciona)"
    r"|(qual\s+[oé]\s+(valor|pre[çc]o|investimento|custo))"
    r"|(quanto\s+custa)"
    r"|(atendem\s+(tamb[eé]m|previdenci[áa]rio|criminal|civil|tribut[áa]rio|trabalhist))"
    r"|(t[eê]m\s+resultado)"
    r"|(j[áa]\s+tiveram)",
    re.IGNORECASE,
)

_TRIGGER_PATTERNS = re.compile(
    r"^(500|800|quero\s+saber\s+mais|tenho\s+interesse|me\s+conta)[\s!?.]*$",
    re.IGNORECASE,
)

_WANTS_PAUSE_PATTERNS = re.compile(
    r"(quero\s+falar\s+com\s+(algu[eé]m|humano|pessoa|atendente))"
    r"|(isso\s+[eé]\s+bot)"
    r"|(fala\s+com\s+(algu[eé]m|pessoa|humano))"
    r"|(n[ãa]o\s+quero\s+(falar\s+com\s+)?bot)"
    r"|(me\s+passa\s+pra\s+algu[eé]m)"
    r"|(quero\s+um\s+humano)"
    r"|(atendente\s+real)"
    r"|(para\s+com\s+iss[oa])"
    r"|(chega\s+de\s+autom[áa]tico)",
    re.IGNORECASE,
)


def _classify_by_keywords(message: str) -> str:
    """Classifica intenção por pattern matching determinístico."""
    msg = message.strip()

    if not msg:
        return "UNKNOWN"

    # Prioridade 1: NO_MONEY (bloqueante)
    if _NO_MONEY_PATTERNS.search(msg):
        return "NO_MONEY"

    # Prioridade 2: NOT_INTERESTED (bloqueante)
    if _NOT_INTERESTED_PATTERNS.search(msg):
        return "NOT_INTERESTED"

    # Prioridade 2.5: WANTS_PAUSE (pede humano, resistência ao bot)
    if _WANTS_PAUSE_PATTERNS.search(msg):
        return "WANTS_PAUSE"

    # Prioridade 3: Pronto para agendar
    if _READY_TO_BOOK_PATTERNS.search(msg):
        return "READY_TO_BOOK"

    # Prioridade 4: Apenas cumprimento
    if _GREETING_PATTERNS.match(msg):
        return "GREETING"

    # Prioridade 5: Gatilho de entrada (tratado como GREETING — inicia Etapa 1)
    if _TRIGGER_PATTERNS.match(msg):
        return "GREETING"

    # Prioridade 6: Pergunta específica (sobre nicho, preço, funcionamento)
    if _QUESTION_PATTERNS.search(msg):
        return "ASKING_SPECIFIC_QUESTION"

    # Default: lead está respondendo algo do SDR
    return "RESPONDING_QUESTION"


async def classify_intent(state: AgentState) -> AgentState:
    """
    Node de classificação de intenção (keyword-based, sem LLM).

    Responsabilidades:
    - Classificar intenção via pattern matching (~0ms vs ~1-3s com LLM)
    - Detectar sinais de NO_MONEY
    - Detectar sinais de pronto para booking
    - A classificação fina é delegada ao LLM no generate_reply
    """
    logger.debug("Classificando intenção (keyword-based)")

    # Se não há mensagem, usar intenção padrão
    if not state.incoming_message:
        state.metadata["intent"] = "UNKNOWN"
        state.metadata["intent_source"] = "no_message"
        return state

    # Se já está em NO_MONEY ou PAUSED, não reclassificar
    if state.current_state.value in ("NO_MONEY", "PAUSED_BY_HUMAN"):
        state.metadata["intent"] = "EXISTING_STATE"
        state.metadata["intent_source"] = "existing_state"
        return state

    # Classificar por keywords
    intent = _classify_by_keywords(state.incoming_message)
    state.metadata["intent"] = intent
    state.metadata["intent_source"] = "keyword"

    logger.debug(f"Intenção classificada (keyword): {intent}")

    # ============================================
    # DETECÇÃO DE NO_MONEY
    # ============================================

    if intent == "NO_MONEY":
        state.no_money_flag = True
        state.metadata["no_money_detected"] = True
        logger.info("🔴 Intenção NO_MONEY detectada (keyword)")

    # ============================================
    # DETECÇÃO DE PRONTO PARA BOOKING
    # ============================================

    if intent == "READY_TO_BOOK":
        state.metadata["ready_to_book"] = True
        logger.info("🟢 Lead pronto para booking (keyword)")

    return state
