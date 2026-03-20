import json
import re
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.resume_template import ResumeTemplate
from app.schemas.schemas import TemplateCreate, TemplateUpdate, TemplateResponse
from app.auth.auth import get_current_user

router = APIRouter()

PLACEHOLDER_PATTERN = re.compile(r"%%([A-Z_]+)%%")


def detect_placeholders(latex_content: str) -> str:
    """Detect %%PLACEHOLDER%% patterns in LaTeX content."""
    found = list(set(PLACEHOLDER_PATTERN.findall(latex_content)))
    return json.dumps(found)


@router.get("/", response_model=List[TemplateResponse])
def list_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(ResumeTemplate).filter(ResumeTemplate.user_id == current_user.id).all()


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    placeholders = detect_placeholders(payload.latex_content)
    template = ResumeTemplate(
        user_id=current_user.id,
        name=payload.name,
        latex_content=payload.latex_content,
        placeholders=placeholders,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tmpl = db.query(ResumeTemplate).filter(
        ResumeTemplate.id == template_id, ResumeTemplate.user_id == current_user.id
    ).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tmpl


@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: str,
    payload: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tmpl = db.query(ResumeTemplate).filter(
        ResumeTemplate.id == template_id, ResumeTemplate.user_id == current_user.id
    ).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")

    if payload.name is not None:
        tmpl.name = payload.name
    if payload.latex_content is not None:
        tmpl.latex_content = payload.latex_content
        tmpl.placeholders = detect_placeholders(payload.latex_content)

    db.commit()
    db.refresh(tmpl)
    return tmpl


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tmpl = db.query(ResumeTemplate).filter(
        ResumeTemplate.id == template_id, ResumeTemplate.user_id == current_user.id
    ).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(tmpl)
    db.commit()
