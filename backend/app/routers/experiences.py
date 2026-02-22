from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.experience import Experience
from app.schemas.schemas import ExperienceCreate, ExperienceUpdate, ExperienceResponse
from app.auth.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[ExperienceResponse])
def list_experiences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Experience).filter(Experience.user_id == current_user.id).all()


@router.post("/", response_model=ExperienceResponse, status_code=status.HTTP_201_CREATED)
def create_experience(
    payload: ExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exp = Experience(user_id=current_user.id, **payload.model_dump())
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


@router.get("/{exp_id}", response_model=ExperienceResponse)
def get_experience(
    exp_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exp = db.query(Experience).filter(Experience.id == exp_id, Experience.user_id == current_user.id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experience not found")
    return exp


@router.put("/{exp_id}", response_model=ExperienceResponse)
def update_experience(
    exp_id: str,
    payload: ExperienceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exp = db.query(Experience).filter(Experience.id == exp_id, Experience.user_id == current_user.id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experience not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(exp, key, value)

    db.commit()
    db.refresh(exp)
    return exp


@router.delete("/{exp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experience(
    exp_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exp = db.query(Experience).filter(Experience.id == exp_id, Experience.user_id == current_user.id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experience not found")
    db.delete(exp)
    db.commit()
