"""
Resume Generation Router.
Orchestrates the full pipeline: JD analysis → skill matching → project ranking →
content generation → guardrail validation → LaTeX compilation → storage.
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
from app.auth.auth import get_current_user
from app.services.jd_analyzer import analyze_job_description
from app.services.skill_matcher import match_skills
from app.services.project_ranker import rank_projects
from app.services.resume_generator import generate_resume_content, fill_template
from app.services.guardrail_validator import validate_resume
from app.services.latex_compiler import compile_latex

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_REGENERATION_ATTEMPTS = 3


@router.post("/generate", response_model=ResumeResponse)
def generate_resume(
    payload: ResumeGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Full resume generation pipeline:
    1. Analyze job description
    2. Match skills against user database
    3. Rank projects by relevance
    4. Generate content for placeholders
    5. Validate against guardrails
    6. Compile LaTeX to PDF
    7. Store the generated resume
    """
    # Get user's template
    template = db.query(ResumeTemplate).filter(
        ResumeTemplate.id == payload.template_id,
        ResumeTemplate.user_id == current_user.id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Get user's data
    user_skills = db.query(Skill).filter(Skill.user_id == current_user.id).all()
    user_projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    user_experiences = db.query(Experience).filter(Experience.user_id == current_user.id).all()

    if not user_skills:
        raise HTTPException(status_code=400, detail="Please add skills to your profile before generating a resume")

    user_skill_names = [s.name for s in user_skills]

    # Step 1: Analyze job description
    try:
        jd_analysis = analyze_job_description(payload.job_description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JD analysis failed: {str(e)}")

    # Step 2: Match skills (hallucination prevention)
    skill_match = match_skills(jd_analysis, user_skill_names)

    # Step 3: Rank projects
    project_rankings = rank_projects(user_projects, jd_analysis, skill_match.matched_skills)

    # Build ranked project data for the generator
    ranked_project_data = []
    for ranking in project_rankings[:5]:
        proj = next((p for p in user_projects if p.id == ranking.project_id), None)
        if proj:
            ranked_project_data.append({
                "title": proj.title,
                "description": proj.description,
                "technologies": proj.technologies,
                "impact": proj.impact,
            })

    # Step 4 & 5: Generate content with retry on validation failure
    latex_output = None
    for attempt in range(MAX_REGENERATION_ATTEMPTS):
        try:
            content = generate_resume_content(
                job_description=payload.job_description,
                matched_skills=skill_match.matched_skills,
                ranked_projects=ranked_project_data,
                experiences=user_experiences,
                domain=jd_analysis.domain,
                seniority=jd_analysis.seniority,
            )

            filled_latex = fill_template(template.latex_content, content, current_user)

            # Prepare authorization list (skills + projects + companies)
            authorized_terms = user_skill_names.copy()
            authorized_terms.extend([p.title for p in user_projects])
            authorized_terms.extend([e.company for e in user_experiences])
            authorized_terms.extend([e.role for e in user_experiences])

            # Guardrail validation
            is_valid, violations = validate_resume(filled_latex, authorized_terms)

            if is_valid:
                latex_output = filled_latex
                break
            else:
                logger.warning(
                    f"Attempt {attempt + 1}: Guardrail violations: {violations}. Regenerating..."
                )

        except Exception as e:
            logger.error(f"Generation attempt {attempt + 1} failed: {e}")
            if attempt == MAX_REGENERATION_ATTEMPTS - 1:
                raise HTTPException(status_code=500, detail=f"Resume generation failed after {MAX_REGENERATION_ATTEMPTS} attempts")

    if latex_output is None:
        raise HTTPException(
            status_code=500,
            detail="Resume generation failed guardrail validation after all attempts"
        )

    # Step 6: Compile LaTeX to PDF
    pdf_path = None
    try:
        pdf_path = compile_latex(latex_output)
    except Exception as e:
        logger.warning(f"LaTeX compilation failed: {e}. Storing LaTeX without PDF.")

    # Step 7: Calculate comprehensive match score
    # score = (required_skill_match * 0.5) + (project_relevance * 0.3) + (keyword_alignment * 0.2)
    avg_project_relevance = 0.0
    if project_rankings:
        avg_project_relevance = sum(r.relevance_score for r in project_rankings[:3]) / min(len(project_rankings), 3)

    keyword_alignment = 0.0
    if jd_analysis.keywords:
        matched_keywords = sum(
            1 for k in jd_analysis.keywords
            if any(k.lower() in s.lower() for s in user_skill_names)
        )
        keyword_alignment = matched_keywords / len(jd_analysis.keywords)

    total_score = (
        (skill_match.required_match_pct / 100 * 0.5) +
        (avg_project_relevance * 0.3) +
        (keyword_alignment * 0.2)
    ) * 100

    # Get existing version count
    existing_count = db.query(GeneratedResume).filter(
        GeneratedResume.user_id == current_user.id,
        GeneratedResume.template_id == payload.template_id,
    ).count()

    # Store the resume
    generated = GeneratedResume(
        user_id=current_user.id,
        template_id=payload.template_id,
        job_description=payload.job_description,
        latex_output=latex_output,
        pdf_path=pdf_path,
        match_score=round(total_score, 1),
        matched_skills=json.dumps(skill_match.matched_skills),
        missing_skills=json.dumps(skill_match.missing_skills),
        metadata_json=json.dumps({
            "jd_analysis": jd_analysis.model_dump(),
            "skill_match": skill_match.model_dump(),
            "project_rankings": [r.model_dump() for r in project_rankings],
            "score_breakdown": {
                "required_skill_match": skill_match.required_match_pct,
                "project_relevance": round(avg_project_relevance * 100, 1),
                "keyword_alignment": round(keyword_alignment * 100, 1),
                "total_score": round(total_score, 1),
            },
        }),
        version=existing_count + 1,
    )
    db.add(generated)
    db.commit()
    db.refresh(generated)

    return generated


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


from app.auth.auth import get_current_user, get_current_user_pdf

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
