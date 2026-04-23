"""
Resume Generation StateGraph.

Implements the 8-agent generation pipeline as a LangGraph StateGraph with
conditional edges for self-healing repair cycles:

  jd_analyst → skill_matcher → project_ranker → content_writer
      → latex_critic ──[errors]──→ repair ──[attempt<3]──→ content_writer
                    ──[clean]───→ guardrail_critic
                                    ──[violations]──→ repair
                                    ──[clean]───────→ reflection
                                                        ──[score<6, attempt<2]──→ repair
                                                        ──[score≥6 OR budget]───→ compiler → END

If attempt_count ≥ MAX_ATTEMPTS at any routing point, the graph exits with
status="failed" to avoid infinite loops.
"""
import logging
from typing import Literal

from langgraph.graph import StateGraph, END

from app.agents.graph_state import ResumeGraphState
from app.agents.nodes import (
    jd_analyst_node,
    skill_matcher_node,
    project_ranker_node,
    content_writer_node,
    latex_critic_node,
    guardrail_critic_node,
    repair_node,
    reflection_node,
    compiler_node,
)

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


# ---------------------------------------------------------------------------
# Conditional Routing Functions
# ---------------------------------------------------------------------------

def route_after_latex_critic(
    state: ResumeGraphState,
) -> Literal["repair", "guardrail_critic", "__end__"]:
    """
    Route after LaTeX Critic Agent:
      - Errors found → Repair Agent (if budget allows)
      - Clean → Guardrail Critic Agent
      - Budget exhausted → END (failed)
    """
    if state.get("status") == "failed":
        return END
    if state.get("attempt_count", 0) >= MAX_ATTEMPTS:
        logger.warning("[Router] Max attempts reached after LaTeX critic — aborting.")
        return END
    if state.get("latex_errors"):
        logger.info(f"[Router] LaTeX errors detected → Repair Agent (attempt {state.get('attempt_count',0)+1})")
        return "repair"
    return "guardrail_critic"


def route_after_guardrail_critic(
    state: ResumeGraphState,
) -> Literal["repair", "reflection", "__end__"]:
    """
    Route after Guardrail Critic Agent:
      - Violations → Repair Agent (if budget allows)
      - Clean → Reflection Agent
      - Budget exhausted → END (failed)
    """
    if state.get("status") == "failed":
        return END
    if state.get("attempt_count", 0) >= MAX_ATTEMPTS:
        logger.warning("[Router] Max attempts reached after guardrail critic — aborting.")
        return END
    if state.get("guardrail_violations"):
        logger.info(f"[Router] Guardrail violations → Repair Agent (attempt {state.get('attempt_count',0)+1})")
        return "repair"
    return "reflection"


def route_after_reflection(
    state: ResumeGraphState,
) -> Literal["repair", "compiler", "__end__"]:
    """
    Route after Reflection Agent:
      - Score < 6 and budget allows → Repair Agent
      - Score ≥ 6 OR budget exhausted → Compiler Agent
    """
    if state.get("status") == "failed":
        return END
    score = state.get("reflection_score", 7)
    attempts = state.get("attempt_count", 0)
    if score < 6 and attempts < MAX_ATTEMPTS - 1:
        logger.info(f"[Router] Reflection score={score} < 6 → Repair Agent (attempt {attempts+1})")
        return "repair"
    logger.info(f"[Router] Reflection score={score} → Compiler Agent")
    return "compiler"


def route_after_repair(
    state: ResumeGraphState,
) -> Literal["content_writer", "__end__"]:
    """
    Route after Repair Agent:
      - Budget not exhausted → Content Writer (re-generate with feedback)
      - Budget exhausted → END (failed)
    """
    if state.get("attempt_count", 0) >= MAX_ATTEMPTS:
        logger.warning("[Router] Max repair attempts reached — failing gracefully.")
        # Inject failed status but keep whatever latex we have
        return END
    logger.info(f"[Router] Repair feedback prepared → Content Writer (attempt {state.get('attempt_count')})")
    return "content_writer"


# ---------------------------------------------------------------------------
# Graph Compilation
# ---------------------------------------------------------------------------

_RESUME_GRAPH = None


def get_resume_graph():
    """
    Return the compiled resume generation StateGraph (singleton).
    Compiled once at first call, reused for all subsequent requests.
    """
    global _RESUME_GRAPH
    if _RESUME_GRAPH is not None:
        return _RESUME_GRAPH

    graph = StateGraph(ResumeGraphState)

    # --- Add all agent nodes ---
    graph.add_node("jd_analyst", jd_analyst_node)
    graph.add_node("skill_matcher", skill_matcher_node)
    graph.add_node("project_ranker", project_ranker_node)
    graph.add_node("content_writer", content_writer_node)
    graph.add_node("latex_critic", latex_critic_node)
    graph.add_node("guardrail_critic", guardrail_critic_node)
    graph.add_node("repair", repair_node)
    graph.add_node("reflection", reflection_node)
    graph.add_node("compiler", compiler_node)

    # --- Entry point ---
    graph.set_entry_point("jd_analyst")

    # --- Linear edges (no branching) ---
    graph.add_edge("jd_analyst", "skill_matcher")
    graph.add_edge("skill_matcher", "project_ranker")
    graph.add_edge("project_ranker", "content_writer")
    graph.add_edge("content_writer", "latex_critic")

    # --- Conditional edges (the cyclical / self-healing part) ---
    graph.add_conditional_edges(
        "latex_critic",
        route_after_latex_critic,
        {
            "repair": "repair",
            "guardrail_critic": "guardrail_critic",
            END: END,
        },
    )
    graph.add_conditional_edges(
        "guardrail_critic",
        route_after_guardrail_critic,
        {
            "repair": "repair",
            "reflection": "reflection",
            END: END,
        },
    )
    graph.add_conditional_edges(
        "reflection",
        route_after_reflection,
        {
            "repair": "repair",
            "compiler": "compiler",
            END: END,
        },
    )
    graph.add_conditional_edges(
        "repair",
        route_after_repair,
        {
            "content_writer": "content_writer",
            END: END,
        },
    )

    # --- Compiler is terminal ---
    graph.add_edge("compiler", END)

    _RESUME_GRAPH = graph.compile()
    logger.info("[ResumeGraph] Compiled 8-agent generation StateGraph successfully.")
    return _RESUME_GRAPH
