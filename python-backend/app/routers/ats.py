from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.auth import get_current_user
from app.models.user import User
from app.services.document_parser import parse_file
from app.services.ats_scorer import score_resume
from app.schemas.schemas import MatchScoreBreakdown

router = APIRouter(prefix="/ats", tags=["ATS"])

@router.post("/score", response_model=MatchScoreBreakdown)
async def score_resume_file(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Score a resume file against a job description.
    Supports .pdf, .docx, and .txt.
    """
    content = await file.read()
    resume_text = parse_file(file.filename, content)
    
    if not resume_text:
        raise HTTPException(
            status_code=400, 
            detail="Failed to extract text from file. Ensure it is a valid .pdf, .docx, or .txt file."
        )
    
    try:
        scoring_result = score_resume(resume_text, job_description)
        return scoring_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
