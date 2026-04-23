"""
Chat Router — powered by the LangGraph 2-agent refinement StateGraph.

The Chat Refiner Agent proposes edits; the Chat Critic Agent validates them.
If violations are found, a second refinement pass is automatically triggered.
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
from app.agents import get_chat_graph

router = APIRouter()


@router.post("/refine", response_model=ChatResponse)
def refine(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Refine a generated resume through interactive chat.

    Agents:
      1. Chat Refiner Agent — proposes edits (honours authorized skill constraints)
      2. Chat Critic Agent  — validates the proposed update against guardrails
         → If violations found, Chat Refiner is automatically re-invoked (max 2 cycles)
    """
    resume = db.query(GeneratedResume).filter(
        GeneratedResume.id == payload.resume_id,
        GeneratedResume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    user_skills = db.query(Skill).filter(Skill.user_id == current_user.id).all()
    authorized_skills = [s.name for s in user_skills]
    chat_history = [{"role": m.role, "content": m.content} for m in payload.history]

    # Build initial ChatGraphState
    initial_state = {
        "message": payload.message,
        "current_latex": resume.latex_output,
        "authorized_skills": authorized_skills,
        "chat_history": chat_history,
        "refinement_attempts": 0,
    }

    try:
        graph = get_chat_graph()
        final_state = graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refinement agent pipeline failed: {str(e)}")

    updated_latex = final_state.get("updated_latex")
    validation_passed = final_state.get("validation_passed", True)
    validation_errors = final_state.get("validation_errors", [])
    reply = final_state.get("reply", "")
    refinement_attempts = final_state.get("refinement_attempts", 1)

    # Append cycle count to reply if multiple attempts were needed
    if refinement_attempts > 1:
        reply += f"\n\n_(Chat Critic triggered {refinement_attempts} refinement cycle(s) to ensure compliance.)_"

    # Persist if valid update
    if updated_latex and validation_passed:
        resume.latex_output = updated_latex
        resume.version += 1
        db.commit()
        db.refresh(resume)

    return ChatResponse(
        reply=reply,
        updated_latex=updated_latex if validation_passed else None,
        validation_passed=validation_passed,
        validation_errors=validation_errors,
    )
