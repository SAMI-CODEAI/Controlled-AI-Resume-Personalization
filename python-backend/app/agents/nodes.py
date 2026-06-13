"""
Agent Node Functions.

Each function is a LangGraph node — it receives the full graph State dict and
returns a *partial* dict with only the fields it modifies. LangGraph merges
the returned partial back into the running state automatically.

All nodes follow the trace contract:
  - Append an AgentTraceEvent to state["agent_trace"] on entry and completion
  - Log structured messages at INFO level for observability
  - Never raise — catch errors and set state["status"] = "failed" instead

Agents implemented here:
  1. jd_analyst_node       — JD Analyst Agent
  2. skill_matcher_node    — Skill Matcher Agent
  3. project_ranker_node   — Project Ranker Agent
  4. content_writer_node   — Content Writer Agent
  5. latex_critic_node     — LaTeX Critic Agent
  6. guardrail_critic_node — Guardrail Critic Agent
  7. repair_node           — Repair Agent
  8. reflection_node       — Reflection Agent
  9. compiler_node         — Compiler Agent
  10. chat_refiner_node    — Chat Refiner Agent
  11. chat_critic_node     — Chat Critic Agent
"""
import logging
import time
from typing import Any, Dict, List, Optional

from app.agents.graph_state import ResumeGraphState, ChatGraphState
from app.agents.tools import (
    analyze_jd_tool,
    match_skills_tool,
    rank_projects_tool,
    generate_content_tool,
    fill_template_tool,
    validate_latex_tool,
    validate_guardrails_tool,
    compile_latex_tool,
    reflection_tool,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Utility: trace helpers
# ---------------------------------------------------------------------------

def _start_event(agent_name: str) -> tuple:
    """Return (start_time, start_event_partial_list)."""
    t0 = time.monotonic()
    logger.info(f"[{agent_name}] Starting...")
    return t0, agent_name


def _end_event(
    agent_name: str,
    t0: float,
    existing_trace: List[Dict],
    details: str,
    errors: Optional[List[str]] = None,
) -> List[Dict]:
    """Build a new trace list with the completed event appended."""
    duration_ms = int((time.monotonic() - t0) * 1000)
    status = "failed" if errors else "completed"
    logger.info(f"[{agent_name}] {status} in {duration_ms}ms. {details}")
    event = {
        "agent": agent_name,
        "status": status,
        "duration_ms": duration_ms,
        "details": details,
        "errors": errors or [],
    }
    return list(existing_trace or []) + [event]


# ---------------------------------------------------------------------------
# 1. JD Analyst Agent
# ---------------------------------------------------------------------------

def jd_analyst_node(state: ResumeGraphState) -> Dict:
    """Parse the job description into structured requirements."""
    AGENT = "JD Analyst Agent"
    t0, _ = _start_event(AGENT)
    try:
        jd_analysis = analyze_jd_tool(state["job_description"])
        trace = _end_event(
            AGENT, t0, state.get("agent_trace", []),
            f"Domain={jd_analysis.get('domain')}, Seniority={jd_analysis.get('seniority')}, "
            f"Keywords={len(jd_analysis.get('keywords', []))}",
        )
        return {
            "jd_analysis": jd_analysis,
            "domain": jd_analysis.get("domain", "software_engineering"),
            "seniority": jd_analysis.get("seniority", "mid"),
            "jd_keywords": jd_analysis.get("keywords", []),
            "agent_trace": trace,
        }
    except Exception as e:
        trace = _end_event(AGENT, t0, state.get("agent_trace", []), "Failed", [str(e)])
        return {"status": "failed", "error_message": f"JD Analyst failed: {e}", "agent_trace": trace}


# ---------------------------------------------------------------------------
# 2. Skill Matcher Agent
# ---------------------------------------------------------------------------

def skill_matcher_node(state: ResumeGraphState) -> Dict:
    """Match user's verified skills against JD requirements."""
    AGENT = "Skill Matcher Agent"
    t0, _ = _start_event(AGENT)
    try:
        user_skill_names = state.get("user_skills", [])
        skill_match = match_skills_tool(state["jd_analysis"], user_skill_names)
        matched = skill_match.get("matched_skills", [])
        missing = skill_match.get("missing_skills", [])
        trace = _end_event(
            AGENT, t0, state.get("agent_trace", []),
            f"Matched={len(matched)}, Missing={len(missing)}, "
            f"RequiredMatchPct={skill_match.get('required_match_pct', 0):.1f}%",
        )
        return {
            "skill_match": skill_match,
            "matched_skills": matched,
            "missing_skills": missing,
            "agent_trace": trace,
        }
    except Exception as e:
        trace = _end_event(AGENT, t0, state.get("agent_trace", []), "Failed", [str(e)])
        return {"status": "failed", "error_message": f"Skill Matcher failed: {e}", "agent_trace": trace}


# ---------------------------------------------------------------------------
# 3. Project Ranker Agent
# ---------------------------------------------------------------------------

def project_ranker_node(state: ResumeGraphState) -> Dict:
    """Score and rank user projects by relevance to the job."""
    AGENT = "Project Ranker Agent"
    t0, _ = _start_event(AGENT)
    try:
        user_projects = state.get("user_projects", [])
        rankings = rank_projects_tool(
            user_projects,
            state["jd_analysis"],
            state.get("matched_skills", []),
        )

        # Build rich project data for the content writer
        ranked_project_data = []
        for ranking in rankings[:5]:
            proj = next(
                (p for p in user_projects if str(getattr(p, "id", None)) == str(ranking.get("project_id"))),
                None,
            )
            if proj:
                ranked_project_data.append({
                    "title": proj.title,
                    "description": proj.description,
                    "technologies": proj.technologies,
                    "impact": proj.impact,
                    "relevance_score": ranking.get("relevance_score", 0),
                })

        trace = _end_event(
            AGENT, t0, state.get("agent_trace", []),
            f"Ranked {len(user_projects)} projects, top-5 selected. "
            f"Top score={rankings[0].get('relevance_score', 0):.2f}" if rankings else "No projects",
        )
        return {
            "project_rankings": rankings,
            "ranked_project_data": ranked_project_data,
            "agent_trace": trace,
        }
    except Exception as e:
        trace = _end_event(AGENT, t0, state.get("agent_trace", []), "Failed", [str(e)])
        return {"status": "failed", "error_message": f"Project Ranker failed: {e}", "agent_trace": trace}


# ---------------------------------------------------------------------------
# 4. Content Writer Agent
# ---------------------------------------------------------------------------

def content_writer_node(state: ResumeGraphState) -> Dict:
    """Generate LaTeX placeholder content and fill the template."""
    AGENT = "Content Writer Agent"
    t0, _ = _start_event(AGENT)
    try:
        from app.database import SessionLocal
        from app.services.document_service import retrieve_relevant_past_impacts
        
        user_id = state.get("user_id") or (state.get("user").id if state.get("user") else None)
        historical_context = []
        if user_id:
            db = SessionLocal()
            try:
                search_query = state.get("job_description", "")
                historical_context = retrieve_relevant_past_impacts(db, user_id, search_query, top_k=3)
            finally:
                db.close()

        content = generate_content_tool(
            job_description=state["job_description"],
            matched_skills=state.get("matched_skills", []),
            ranked_project_data=state.get("ranked_project_data", []),
            experiences=state.get("user_experiences", []),
            domain=state.get("domain", "software_engineering"),
            seniority=state.get("seniority", "mid"),
            repair_feedback=state.get("repair_feedback"),  # None on first pass
            historical_context=historical_context,
        )
        filled_latex = fill_template_tool(
            state["template_latex"],
            content,
            state.get("user"),
        )
        sections_generated = [k for k, v in content.items() if v.strip()]
        trace = _end_event(
            AGENT, t0, state.get("agent_trace", []),
            f"Generated sections: {sections_generated}. "
            f"LaTeX length={len(filled_latex)} chars. "
            f"{'(Repair pass)' if state.get('repair_feedback') else '(Initial pass)'}",
        )
        return {
            "generated_content": content,
            "filled_latex": filled_latex,
            "repair_feedback": None,  # clear feedback after use
            "agent_trace": trace,
        }
    except Exception as e:
        trace = _end_event(AGENT, t0, state.get("agent_trace", []), "Failed", [str(e)])
        return {"status": "failed", "error_message": f"Content Writer failed: {e}", "agent_trace": trace}


# ---------------------------------------------------------------------------
# 5. LaTeX Critic Agent
# ---------------------------------------------------------------------------

def latex_critic_node(state: ResumeGraphState) -> Dict:
    """Validate LaTeX structural correctness. Catch unbalanced environments."""
    AGENT = "LaTeX Critic Agent"
    t0, _ = _start_event(AGENT)
    content = state.get("generated_content") or {}
    latex_errors = validate_latex_tool(content)
    details = (
        f"PASS — All {len(content)} sections structurally valid."
        if not latex_errors
        else f"FAIL — {len(latex_errors)} error(s): {latex_errors[:3]}"
    )
    trace = _end_event(AGENT, t0, state.get("agent_trace", []), details, latex_errors or None)
    return {"latex_errors": latex_errors, "agent_trace": trace}


# ---------------------------------------------------------------------------
# 6. Guardrail Critic Agent
# ---------------------------------------------------------------------------

def guardrail_critic_node(state: ResumeGraphState) -> Dict:
    """Detect unauthorized skills/entities in the filled LaTeX — anti-hallucination."""
    AGENT = "Guardrail Critic Agent"
    t0, _ = _start_event(AGENT)
    filled_latex = state.get("filled_latex", "")
    authorized_terms = state.get("authorized_terms", [])
    is_valid, violations = validate_guardrails_tool(filled_latex, authorized_terms, strict=True)
    details = (
        "PASS — No unauthorized entities detected."
        if is_valid
        else f"FAIL — {len(violations)} violation(s): {violations[:5]}"
    )
    trace = _end_event(AGENT, t0, state.get("agent_trace", []), details, violations if violations else None)
    return {"guardrail_violations": violations, "agent_trace": trace}


# ---------------------------------------------------------------------------
# 7. Repair Agent
# ---------------------------------------------------------------------------

def repair_node(state: ResumeGraphState) -> Dict:
    """
    Self-healing agent: builds a repair prompt from accumulated critic feedback
    and increments the attempt counter. The feedback is consumed by the next
    Content Writer pass via generate_content_tool(repair_feedback=...).
    """
    AGENT = "Repair Agent"
    t0, _ = _start_event(AGENT)
    attempt = state.get("attempt_count", 0) + 1
    latex_errors = state.get("latex_errors") or []
    violations = state.get("guardrail_violations") or []
    reflection_critique = state.get("reflection_critique") or ""

    feedback_parts = []
    if latex_errors:
        feedback_parts.append(f"LaTeX structural errors to fix:\n" + "\n".join(f"  - {e}" for e in latex_errors))
    if violations:
        feedback_parts.append(
            f"Unauthorized entities detected (REMOVE these entirely):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )
    if reflection_critique and "score" in reflection_critique.lower():
        feedback_parts.append(f"Quality critique:\n{reflection_critique}")

    repair_feedback = "\n\n".join(feedback_parts) if feedback_parts else "General quality improvement requested."
    details = f"Attempt #{attempt}. Feedback prepared: {len(feedback_parts)} issue category(ies)."
    trace = _end_event(AGENT, t0, state.get("agent_trace", []), details)
    return {
        "repair_feedback": repair_feedback,
        "attempt_count": attempt,
        "latex_errors": [],          # reset critics for next pass
        "guardrail_violations": [],
        "reflection_critique": None,
        "agent_trace": trace,
    }


# ---------------------------------------------------------------------------
# 8. Reflection Agent
# ---------------------------------------------------------------------------

def reflection_node(state: ResumeGraphState) -> Dict:
    """
    Meta-evaluation agent: asks the LLM to score resume quality 1-10.
    Score < 6 triggers another repair cycle (if attempt budget allows).
    """
    AGENT = "Reflection Agent"
    t0, _ = _start_event(AGENT)
    try:
        score, critique = reflection_tool(
            filled_latex=state.get("filled_latex", ""),
            job_description=state.get("job_description", ""),
            matched_skills=state.get("matched_skills", []),
        )
        details = f"Quality score={score}/10. {'Recommending repair.' if score < 6 else 'Approved for compilation.'}"
        trace = _end_event(AGENT, t0, state.get("agent_trace", []), details)
        return {
            "reflection_score": score,
            "reflection_critique": critique if score < 6 else None,
            "agent_trace": trace,
        }
    except Exception as e:
        trace = _end_event(AGENT, t0, state.get("agent_trace", []), "Reflection failed, defaulting to 7", [str(e)])
        return {"reflection_score": 7, "reflection_critique": None, "agent_trace": trace}


# ---------------------------------------------------------------------------
# 9. Compiler Agent
# ---------------------------------------------------------------------------

def compiler_node(state: ResumeGraphState) -> Dict:
    """Compile the final validated LaTeX document to PDF."""
    AGENT = "Compiler Agent"
    t0, _ = _start_event(AGENT)
    pdf_path = compile_latex_tool(state.get("filled_latex", ""))
    if pdf_path and pdf_path.endswith(".pdf"):
        details = f"PDF compiled successfully: {pdf_path}"
        trace = _end_event(AGENT, t0, state.get("agent_trace", []), details)
        return {"pdf_path": pdf_path, "status": "success", "agent_trace": trace}
    else:
        details = "PDF compilation unavailable — storing LaTeX source only."
        trace = _end_event(AGENT, t0, state.get("agent_trace", []), details, ["pdflatex not available"])
        return {"pdf_path": pdf_path, "status": "success", "agent_trace": trace}


# ---------------------------------------------------------------------------
# 10. Chat Refiner Agent
# ---------------------------------------------------------------------------

def chat_refiner_node(state: ChatGraphState) -> Dict:
    """Process a user refinement message, returning an updated LaTeX draft."""
    AGENT = "Chat Refiner Agent"
    t0 = time.monotonic()
    logger.info(f"[{AGENT}] Processing refinement: '{state.get('message', '')[:80]}...'")
    try:
        from app.services.chat_refiner import refine_resume
        reply, updated_latex, validation_passed, validation_errors = refine_resume(
            message=state["message"],
            current_latex=state["current_latex"],
            authorized_terms=state.get("authorized_terms", []),
            chat_history=state.get("chat_history", []),
        )
        duration_ms = int((time.monotonic() - t0) * 1000)
        logger.info(f"[{AGENT}] Completed in {duration_ms}ms. Changes={'yes' if updated_latex else 'no'}")
        return {
            "updated_latex": updated_latex,
            "reply": reply,
            "changes_made": updated_latex is not None,
            "validation_passed": validation_passed,
            "validation_errors": validation_errors,
            "refinement_attempts": state.get("refinement_attempts", 0) + 1,
        }
    except Exception as e:
        logger.error(f"[{AGENT}] Failed: {e}")
        return {
            "reply": f"Refinement temporarily unavailable: {e}",
            "updated_latex": None,
            "validation_passed": False,
            "validation_errors": [str(e)],
        }


# ---------------------------------------------------------------------------
# 11. Chat Critic Agent
# ---------------------------------------------------------------------------

def chat_critic_node(state: ChatGraphState) -> Dict:
    """
    Validate the chat refiner's proposed LaTeX update against guardrails.
    If violations are found and attempt budget allows, triggers a re-refinement.
    """
    AGENT = "Chat Critic Agent"
    t0 = time.monotonic()
    logger.info(f"[{AGENT}] Validating proposed update...")
    updated_latex = state.get("updated_latex")
    if not updated_latex:
        # Nothing to validate — refiner made no changes or was blocked
        logger.info(f"[{AGENT}] No update to validate — skipping.")
        return {"validation_passed": True, "validation_errors": []}

    authorized = state.get("authorized_terms", [])
    is_valid, violations = validate_guardrails_tool(updated_latex, authorized, strict=True)
    duration_ms = int((time.monotonic() - t0) * 1000)
    logger.info(f"[{AGENT}] Completed in {duration_ms}ms. Valid={is_valid}, Violations={violations}")
    return {"validation_passed": is_valid, "validation_errors": violations}
