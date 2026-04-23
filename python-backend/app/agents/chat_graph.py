"""
Chat Refinement StateGraph.

Implements the two-agent chat refinement loop:

  chat_refiner → chat_critic ──[violations, attempt<2]──→ chat_refiner
                              ──[passes OR exhausted]──→ END

The Chat Refiner Agent proposes edits; the Chat Critic Agent validates them
against the user's authorized skill set. If violations are found on the first
attempt, the refiner is called again with the violation list injected.
After 2 attempts, whatever state we have is accepted so the user isn't blocked.
"""
import logging
from typing import Literal

from langgraph.graph import StateGraph, END

from app.agents.graph_state import ChatGraphState
from app.agents.nodes import chat_refiner_node, chat_critic_node

logger = logging.getLogger(__name__)

MAX_REFINEMENT_ATTEMPTS = 2


# ---------------------------------------------------------------------------
# Conditional Routing
# ---------------------------------------------------------------------------

def route_after_chat_critic(
    state: ChatGraphState,
) -> Literal["chat_refiner", "__end__"]:
    """
    Route after Chat Critic:
      - Violations and budget remaining → Chat Refiner (self-correct)
      - Clean or budget exhausted → END
    """
    violations = state.get("validation_errors", [])
    attempts = state.get("refinement_attempts", 0)

    if violations and attempts < MAX_REFINEMENT_ATTEMPTS:
        logger.info(
            f"[ChatRouter] Chat critic found {len(violations)} violation(s) "
            f"→ re-refining (attempt {attempts + 1})"
        )
        return "chat_refiner"

    if violations:
        logger.info(f"[ChatRouter] Budget exhausted with violations — accepting current state.")
    else:
        logger.info(f"[ChatRouter] Chat critic passed → END")
    return END


# ---------------------------------------------------------------------------
# Graph Compilation
# ---------------------------------------------------------------------------

_CHAT_GRAPH = None


def get_chat_graph():
    """
    Return the compiled chat refinement StateGraph (singleton).
    """
    global _CHAT_GRAPH
    if _CHAT_GRAPH is not None:
        return _CHAT_GRAPH

    graph = StateGraph(ChatGraphState)

    graph.add_node("chat_refiner", chat_refiner_node)
    graph.add_node("chat_critic", chat_critic_node)

    graph.set_entry_point("chat_refiner")

    graph.add_edge("chat_refiner", "chat_critic")
    graph.add_conditional_edges(
        "chat_critic",
        route_after_chat_critic,
        {
            "chat_refiner": "chat_refiner",
            END: END,
        },
    )

    _CHAT_GRAPH = graph.compile()
    logger.info("[ChatGraph] Compiled 2-agent chat refinement StateGraph successfully.")
    return _CHAT_GRAPH
