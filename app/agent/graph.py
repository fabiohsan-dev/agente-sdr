"""LangGraph do agente SDR.

NOTA: LangGraph não requer chave de API própria.
Ele usa a chave do provedor de LLM (OpenAI, Anthropic, etc.)
configurada nas integrações correspondentes.
"""

import logging
from typing import Literal

from langgraph.graph import END, StateGraph

from app.agent.nodes import (
    apply_hard_rules,
    classify_intent,
    decide_stage,
    finalize,
    generate_reply,
    ingest_message,
    load_state,
    maybe_call_tools,
    maybe_process_media,
    persist_decision,
)
from app.state.lead_states import AgentState

logger = logging.getLogger(__name__)


def create_agent_graph() -> StateGraph:
    """
    Cria o grafo do agente LangGraph.

    NOTA: LangGraph usa a chave da OpenAI configurada em
    app.integrations.openai.client.get_openai_client()

    Fluxo:
    1. ingest_message → 2. load_state → 3. apply_hard_rules →
    4. maybe_process_media → 5. classify_intent → 6. decide_stage →
    7. maybe_call_tools → 8. generate_reply → 9. persist_decision →
    10. finalize → END
    """

    # ============================================
    # CRIAR GRAPH
    # ============================================

    workflow = StateGraph(AgentState)

    # ============================================
    # ADICIONAR NODES
    # ============================================

    workflow.add_node("ingest_message", ingest_message.ingest_message)
    workflow.add_node("load_state", load_state.load_state)
    workflow.add_node("apply_hard_rules", apply_hard_rules.apply_hard_rules)
    workflow.add_node("maybe_process_media", maybe_process_media.maybe_process_media)
    workflow.add_node("classify_intent", classify_intent.classify_intent)
    workflow.add_node("decide_stage", decide_stage.decide_stage)
    workflow.add_node("maybe_call_tools", maybe_call_tools.maybe_call_tools)
    workflow.add_node("generate_reply", generate_reply.generate_reply)
    workflow.add_node("persist_decision", persist_decision.persist_decision)
    workflow.add_node("finalize", finalize.finalize)

    # ============================================
    # DEFINIR EDGES
    # ============================================

    # Fluxo principal sequencial
    workflow.set_entry_point("ingest_message")

    workflow.add_edge("ingest_message", "load_state")
    workflow.add_edge("load_state", "apply_hard_rules")
    workflow.add_edge("apply_hard_rules", "maybe_process_media")
    workflow.add_edge("maybe_process_media", "classify_intent")
    workflow.add_edge("classify_intent", "decide_stage")
    workflow.add_edge("decide_stage", "maybe_call_tools")
    workflow.add_edge("maybe_call_tools", "generate_reply")
    workflow.add_edge("generate_reply", "persist_decision")
    workflow.add_edge("persist_decision", "finalize")
    workflow.add_edge("finalize", END)

    # ============================================
    # COMPILAR
    # ============================================

    app = workflow.compile()
    logger.info("Graph do agente compilado com sucesso")

    return app


# Singleton global
_agent_graph: StateGraph | None = None


def get_agent_graph() -> StateGraph:
    """Retorna instância singleton do graph do agente."""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = create_agent_graph()
    return _agent_graph


async def run_agent(state: AgentState) -> AgentState:
    """
    Executa o agente com um estado inicial.

    Args:
        state: Estado inicial do agente

    Returns:
        Estado final após execução completa
    """
    graph = get_agent_graph()
    result = await graph.ainvoke(state.model_dump())
    return AgentState(**result)


def check_llm_configuration() -> bool:
    """
    Verifica se o LLM está configurado corretamente.

    LangGraph usa a chave da OpenAI, não tem chave própria.

    Returns:
        True se configurado corretamente
    """
    try:
        from app.config.settings import get_settings
        settings = get_settings()

        # Verificar se OpenAI está configurada
        if not settings.openai_api_key:
            logger.error("OPENAI_API_KEY não configurada")
            return False

        logger.info(f"LLM configurado: {settings.openai_model}")
        return True

    except Exception as e:
        logger.error(f"Erro ao verificar configuração do LLM: {e}")
        return False


# ============================================
# EXPORT PARA LANGGRAPH CLOUD
# ============================================
# langgraph.json referencia "graph.py:graph"
# O LangGraph Platform exige um objeto compilado no nível do módulo.

graph = create_agent_graph()

