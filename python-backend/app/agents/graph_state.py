"""
Graph State Definitions.

Shared TypedDict schemas for all LangGraph StateGraph instances in this platform.
Every agent node reads from and writes back to these typed state dictionaries.
LangGraph merges partial dicts returned by nodes — no field is clobbered unless
the node explicitly returns it.
"""
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


# ---------------------------------------------------------------------------
# Per-step agent trace event (used for observability)
# ---------------------------------------------------------------------------

class AgentTraceEvent(TypedDict, total=False):
    agent: str          # e.g., "JD Analyst Agent"
    status: str         # "started" | "completed" | "failed"
    duration_ms: int    # wall-clock time in milliseconds
    details: str        # short human-readable summary of what was done
    errors: List[str]   # any errors encountered in this step


# ---------------------------------------------------------------------------
# Generation Graph State
# ---------------------------------------------------------------------------

class ResumeGraphState(TypedDict, total=False):
    # --- Inputs: provided by the router before graph.invoke() ---
    job_description: str
    template_latex: str
    authorized_terms: List[str]          # skills + project titles + companies
    user: Any                            # ORM User object (for fill_template)
    user_skills: List[str]               # raw skill name list
    user_projects: List[Any]             # ORM Project objects
    user_experiences: List[Any]          # ORM Experience objects
    template_id: str
    user_id: str

    # --- Set by JD Analyst Agent ---
    jd_analysis: Optional[Dict[str, Any]]  # full JDAnalysis model dict
    domain: Optional[str]
    seniority: Optional[str]
    jd_keywords: Optional[List[str]]

    # --- Set by Skill Matcher Agent ---
    skill_match: Optional[Dict[str, Any]]  # SkillMatch model dict
    matched_skills: Optional[List[str]]
    missing_skills: Optional[List[str]]

    # --- Set by Project Ranker Agent ---
    project_rankings: Optional[List[Dict[str, Any]]]  # ProjectRanking model dicts
    ranked_project_data: Optional[List[Dict[str, Any]]]  # {title, description, ...}

    # --- Set by Content Writer Agent ---
    generated_content: Optional[Dict[str, str]]    # {summary, skills, projects, experiences}
    filled_latex: Optional[str]

    # --- Set by LaTeX Critic Agent ---
    latex_errors: Optional[List[str]]

    # --- Set by Guardrail Critic Agent ---
    guardrail_violations: Optional[List[str]]

    # --- Set by Repair Agent ---
    repair_feedback: Optional[str]   # injected into re-generation prompt
    attempt_count: int               # increments each repair cycle

    # --- Set by Reflection Agent ---
    reflection_score: Optional[int]       # 1-10 LLM quality score
    reflection_critique: Optional[str]    # LLM critique text

    # --- Set by Compiler Agent ---
    pdf_path: Optional[str]

    # --- Terminal fields ---
    status: Optional[str]          # "success" | "failed"
    error_message: Optional[str]

    # --- Observability ---
    agent_trace: List[AgentTraceEvent]


# ---------------------------------------------------------------------------
# Chat Refinement Graph State
# ---------------------------------------------------------------------------

class ChatGraphState(TypedDict, total=False):
    # --- Inputs ---
    message: str
    current_latex: str
    authorized_skills: List[str]
    chat_history: List[Dict[str, str]]   # [{role, content}, ...]

    # --- Set by Chat Refiner Agent ---
    updated_latex: Optional[str]
    reply: Optional[str]
    changes_made: bool

    # --- Set by Chat Critic Agent ---
    validation_passed: bool
    validation_errors: List[str]

    # --- Loop control ---
    refinement_attempts: int
