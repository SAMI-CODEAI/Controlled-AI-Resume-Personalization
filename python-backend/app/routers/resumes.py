"""
Resume Generation Router.

All orchestration is now delegated to the LangGraph 8-agent StateGraph.
The router's sole responsibilities are:
  1. Validate request and fetch DB entities
  2. Build the initial ResumeGraphState
  3. Invoke the graph
  4. Persist results and compute match score
  5. Return the response
"""
import json
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.skill import Skill
from app.models.project import Project
from app.models.experience import Experience
from app.models.resume_template import ResumeTemplate
from app.models.generated_resume import GeneratedResume
from app.schemas.schemas import (
    ResumeGenerateRequest, ResumeResponse, MatchScoreBreakdown,
)
from app.auth.auth import get_current_user, get_current_user_pdf
from app.agents import get_resume_graph, AgentMemory
from app.agents.agent_memory import save_trace

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=ResumeResponse)
def generate_resume(
    payload: ResumeGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Resume generation endpoint — now powered by the 8-agent LangGraph pipeline.

    Agents executed (in order, with self-healing loops):
      1. JD Analyst Agent       — parses job description
      2. Skill Matcher Agent    — anti-hallucination skill filtering
      3. Project Ranker Agent   — relevance scoring
      4. Content Writer Agent   — LaTeX generation (with repair-feedback injection)
      5. LaTeX Critic Agent     — structural validation (triggers repair loop)
      6. Guardrail Critic Agent — hallucination detection (triggers repair loop)
      7. Repair Agent           — self-heals with error context (≤3 cycles)
      8. Reflection Agent       — quality scoring (triggers repair if score<6)
      9. Compiler Agent         — LaTeX → PDF
    """
    # --- Fetch template ---
    template = db.query(ResumeTemplate).filter(
        ResumeTemplate.id == payload.template_id,
        ResumeTemplate.user_id == current_user.id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # --- Fetch user data ---
    user_skills = db.query(Skill).filter(Skill.user_id == current_user.id).all()
    user_projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    user_experiences = db.query(Experience).filter(Experience.user_id == current_user.id).all()

    if not user_skills:
        raise HTTPException(
            status_code=400,
            detail="Please add skills to your profile before generating a resume",
        )

    user_skill_names = [s.name for s in user_skills]

    # Build authorized terms for guardrail agent
    authorized_terms: List[str] = (
        user_skill_names
        + [p.title for p in user_projects]
        + [e.company for e in user_experiences]
        + [e.role for e in user_experiences]
    )

    # --- Build initial graph state ---
    initial_state = {
        "job_description": payload.job_description,
        "template_latex": template.latex_content,
        "authorized_terms": authorized_terms,
        "user": current_user,
        "user_skills": user_skill_names,
        "user_projects": user_projects,
        "user_experiences": user_experiences,
        "template_id": str(payload.template_id),
        "user_id": str(current_user.id),
        "attempt_count": 0,
        "agent_trace": [],
    }

    # --- Invoke the multi-agent graph ---
    logger.info(
        f"[ResumeRouter] Invoking 8-agent graph for user={current_user.id} "
        f"template={payload.template_id}"
    )
    try:
        graph = get_resume_graph()
        final_state = graph.invoke(initial_state)
    except Exception as e:
        logger.error(f"[ResumeRouter] Graph invocation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent pipeline failed: {str(e)}")

    # --- Check for pipeline failure ---
    if final_state.get("status") == "failed":
        error_msg = final_state.get("error_message", "Unknown agent error")
        logger.error(f"[ResumeRouter] Graph completed with status=failed: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Resume generation failed after max repair attempts. Last error: {error_msg}",
        )

    filled_latex = final_state.get("filled_latex", "")
    if not filled_latex:
        raise HTTPException(status_code=500, detail="No LaTeX output produced by agent pipeline")

    pdf_path = final_state.get("pdf_path")
    agent_trace = final_state.get("agent_trace", [])
    reflection_score = final_state.get("reflection_score")
    attempt_count = final_state.get("attempt_count", 0)

    # --- Update agent memory ---
    memory = AgentMemory(str(current_user.id))
    memory.record_generation(
        domain=final_state.get("domain", "unknown"),
        matched_skills=final_state.get("matched_skills", []),
        reflection_score=reflection_score,
        attempt_count=attempt_count,
        status=final_state.get("status", "success"),
    )

    # --- Calculate comprehensive match score ---
    skill_match = final_state.get("skill_match", {})
    project_rankings = final_state.get("project_rankings", [])

    avg_project_relevance = 0.0
    if project_rankings:
        avg_project_relevance = sum(
            r.get("relevance_score", 0) for r in project_rankings[:3]
        ) / min(len(project_rankings), 3)

    jd_keywords = final_state.get("jd_keywords", [])
    keyword_alignment = 0.0
    if jd_keywords:
        matched_kw = sum(
            1 for k in jd_keywords
            if any(k.lower() in s.lower() for s in user_skill_names)
        )
        keyword_alignment = matched_kw / len(jd_keywords)

    required_match_pct = skill_match.get("required_match_pct", 0)
    total_score = (
        (required_match_pct / 100 * 0.5)
        + (avg_project_relevance * 0.3)
        + (keyword_alignment * 0.2)
    ) * 100

    # --- Store the generated resume ---
    existing_count = db.query(GeneratedResume).filter(
        GeneratedResume.user_id == current_user.id,
        GeneratedResume.template_id == payload.template_id,
    ).count()

    generated = GeneratedResume(
        user_id=current_user.id,
        template_id=payload.template_id,
        job_description=payload.job_description,
        latex_output=filled_latex,
        pdf_path=pdf_path,
        match_score=round(total_score, 1),
        matched_skills=json.dumps(final_state.get("matched_skills", [])),
        missing_skills=json.dumps(final_state.get("missing_skills", [])),
        metadata_json=json.dumps({
            "jd_analysis": final_state.get("jd_analysis", {}),
            "skill_match": skill_match,
            "project_rankings": project_rankings,
            "score_breakdown": {
                "required_skill_match": required_match_pct,
                "project_relevance": round(avg_project_relevance * 100, 1),
                "keyword_alignment": round(keyword_alignment * 100, 1),
                "total_score": round(total_score, 1),
            },
            # NEW: agentic metadata
            "reflection_score": reflection_score,
            "repair_cycles": attempt_count,
            "agent_memory_snapshot": memory.snapshot(),
            "agent_trace": agent_trace,
        }),
        version=existing_count + 1,
    )
    db.add(generated)
    db.commit()
    db.refresh(generated)

    # Persist trace to disk asynchronously (best-effort)
    save_trace(str(current_user.id), str(generated.id), agent_trace)

    logger.info(
        f"[ResumeRouter] Resume {generated.id} generated successfully. "
        f"Score={total_score:.1f} Reflection={reflection_score}/10 "
        f"Repair cycles={attempt_count}"
    )
    return generated


# ---------------------------------------------------------------------------
# Remaining CRUD endpoints (unchanged API surface)
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[ResumeResponse])
def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all generated resumes for the current user."""
    return db.query(GeneratedResume).filter(
        GeneratedResume.user_id == current_user.id
    ).order_by(GeneratedResume.created_at.desc()).all()


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific generated resume."""
    resume = db.query(GeneratedResume).filter(
        GeneratedResume.id == resume_id,
        GeneratedResume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.get("/{resume_id}/pdf")
def download_pdf(
    resume_id: str,
    current_user: User = Depends(get_current_user_pdf),
    db: Session = Depends(get_db),
):
    """Download the PDF for a generated resume."""
    resume = db.query(GeneratedResume).filter(
        GeneratedResume.id == resume_id,
        GeneratedResume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.pdf_path or not resume.pdf_path.endswith(".pdf"):
        raise HTTPException(status_code=404, detail="PDF not available for this resume")
    return FileResponse(
        resume.pdf_path,
        media_type="application/pdf",
        filename=f"resume_v{resume.version}.pdf",
    )


@router.get("/{resume_id}/analysis", response_model=MatchScoreBreakdown)
def get_analysis(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the full match score analysis for a generated resume."""
    resume = db.query(GeneratedResume).filter(
        GeneratedResume.id == resume_id,
        GeneratedResume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.metadata_json:
        raise HTTPException(status_code=404, detail="Analysis not available")

    metadata = json.loads(resume.metadata_json)
    breakdown = metadata.get("score_breakdown", {})
    skill_match = metadata.get("skill_match", {})
    rankings = metadata.get("project_rankings", [])

    from app.schemas.schemas import ProjectRanking
    return MatchScoreBreakdown(
        required_skill_match=breakdown.get("required_skill_match", 0),
        project_relevance=breakdown.get("project_relevance", 0),
        keyword_alignment=breakdown.get("keyword_alignment", 0),
        total_score=breakdown.get("total_score", 0),
        matched_skills=skill_match.get("matched_skills", []),
        missing_skills=skill_match.get("missing_skills", []),
        ranked_projects=[ProjectRanking(**r) for r in rankings],
        improvement_suggestions=skill_match.get("improvement_suggestions", []),
    )


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a generated resume."""
    resume = db.query(GeneratedResume).filter(
        GeneratedResume.id == resume_id,
        GeneratedResume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    db.delete(resume)
    db.commit()
