from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.achievement import Achievement
from app.schemas.schemas import AchievementCreate, AchievementUpdate, AchievementResponse
from app.auth.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[AchievementResponse])
def list_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Achievement).filter(Achievement.user_id == current_user.id).all()


@router.post("/", response_model=AchievementResponse, status_code=status.HTTP_201_CREATED)
def create_achievement(
    payload: AchievementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ach = Achievement(user_id=current_user.id, **payload.model_dump())
    db.add(ach)
    db.commit()
    db.refresh(ach)
    return ach


@router.put("/{ach_id}", response_model=AchievementResponse)
def update_achievement(
    ach_id: str,
    payload: AchievementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ach = db.query(Achievement).filter(Achievement.id == ach_id, Achievement.user_id == current_user.id).first()
    if not ach:
        raise HTTPException(status_code=404, detail="Achievement not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(ach, key, value)

    db.commit()
    db.refresh(ach)
    return ach


@router.delete("/{ach_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_achievement(
    ach_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ach = db.query(Achievement).filter(Achievement.id == ach_id, Achievement.user_id == current_user.id).first()
    if not ach:
        raise HTTPException(status_code=404, detail="Achievement not found")
    db.delete(ach)
    db.commit()
