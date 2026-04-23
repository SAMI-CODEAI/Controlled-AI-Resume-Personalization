"""
Agent Memory Module.

Provides lightweight session memory for the multi-agent pipeline:
  - In-memory per-user session state (hot path, cleared on restart)
  - Persistent JSON trace logs written to output/traces/ (cold path, survives restarts)

The memory is intentionally simple — no vector DB required. Its role is to:
  1. Carry context between successive generate calls in the same session
     (e.g., skip re-analysis if the domain hasn't changed).
  2. Persist structured agent traces so devs can debug multi-hop reasoning.
"""
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global in-memory store  {user_id: MemoryEntry}
# ---------------------------------------------------------------------------
_MEMORY_STORE: Dict[str, Dict[str, Any]] = {}

# Where to write trace JSON files
_TRACE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "output", "traces"
)


class AgentMemory:
    """
    Per-user session memory accessed by agent nodes during a graph run.

    Usage inside a node:
        memory = AgentMemory(user_id)
        last_domain = memory.get("last_domain")
        memory.set("last_domain", "software_engineering")
    """

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        if user_id not in _MEMORY_STORE:
            _MEMORY_STORE[user_id] = {
                "last_domain": None,
                "last_matched_skills": [],
                "reflection_scores": [],          # last 5 scores
                "generation_summaries": [],        # last 5 concise summaries
                "total_generations": 0,
                "total_repair_cycles": 0,
            }

    def get(self, key: str, default: Any = None) -> Any:
        return _MEMORY_STORE[self.user_id].get(key, default)

    def set(self, key: str, value: Any) -> None:
        _MEMORY_STORE[self.user_id][key] = value

    def record_generation(
        self,
        domain: str,
        matched_skills: List[str],
        reflection_score: Optional[int],
        attempt_count: int,
        status: str,
    ) -> None:
        """Append a generation summary to memory after a graph run completes."""
        store = _MEMORY_STORE[self.user_id]
        store["last_domain"] = domain
        store["last_matched_skills"] = matched_skills
        store["total_generations"] = store.get("total_generations", 0) + 1
        store["total_repair_cycles"] = store.get("total_repair_cycles", 0) + max(0, attempt_count - 1)

        if reflection_score is not None:
            scores = store.get("reflection_scores", [])
            scores.append(reflection_score)
            store["reflection_scores"] = scores[-5:]  # keep last 5

        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "domain": domain,
            "matched_skills_count": len(matched_skills),
            "reflection_score": reflection_score,
            "attempt_count": attempt_count,
            "status": status,
        }
        summaries = store.get("generation_summaries", [])
        summaries.append(summary)
        store["generation_summaries"] = summaries[-5:]

    def get_average_reflection_score(self) -> Optional[float]:
        """Return the running average reflection score or None if no history."""
        scores = _MEMORY_STORE[self.user_id].get("reflection_scores", [])
        if not scores:
            return None
        return round(sum(scores) / len(scores), 1)

    def snapshot(self) -> Dict[str, Any]:
        """Return a read-only snapshot of this user's memory."""
        return dict(_MEMORY_STORE.get(self.user_id, {}))


# ---------------------------------------------------------------------------
# Trace persistence
# ---------------------------------------------------------------------------

def save_trace(
    user_id: str,
    resume_id: str,
    trace: List[Dict[str, Any]],
) -> Optional[str]:
    """
    Persist agent_trace to a JSON file in output/traces/.
    Returns the file path, or None if write fails.
    """
    try:
        os.makedirs(_TRACE_DIR, exist_ok=True)
        filename = f"{user_id}_{resume_id}_{int(time.time())}.json"
        filepath = os.path.join(_TRACE_DIR, filename)
        payload = {
            "user_id": user_id,
            "resume_id": resume_id,
            "generated_at": datetime.utcnow().isoformat(),
            "trace": trace,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        logger.info(f"[AgentMemory] Trace saved: {filepath}")
        return filepath
    except Exception as e:
        logger.warning(f"[AgentMemory] Failed to save trace: {e}")
        return None
