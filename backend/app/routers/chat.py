"""
Chat Router for interactive AI resume refinement.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.skill import Skill
from app.models.generated_resume import GeneratedResume
from app.schemas.schemas import ChatRequest, ChatResponse
from app.auth.auth import get_current_user
from app.services.chat_refiner import refine_resume

router = APIRouter()


@router.post("/refine", response_model=ChatResponse)
def refine(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Refine a generated resume through interactive chat.
    All modifications are validated against the user's skill database.
    """
    # Get the resume
    resume = db.query(GeneratedResume).filter(
        GeneratedResume.id == payload.resume_id,
        GeneratedResume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Get user's authorized skills
    user_skills = db.query(Skill).filter(Skill.user_id == current_user.id).all()
    authorized_skills = [s.name for s in user_skills]

    # Process refinement
    chat_history = [{"role": m.role, "content": m.content} for m in payload.history]

    try:
        reply, updated_latex, validation_passed, validation_errors = refine_resume(
            message=payload.message,
            current_latex=resume.latex_output,
            authorized_skills=authorized_skills,
            chat_history=chat_history,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refinement failed: {str(e)}")

    # If valid update, save the new version
    if updated_latex and validation_passed:
        resume.latex_output = updated_latex
        resume.version += 1
        db.commit()
        db.refresh(resume)

    return ChatResponse(
        reply=reply,
        updated_latex=updated_latex,
        validation_passed=validation_passed,
        validation_errors=validation_errors,
    )
