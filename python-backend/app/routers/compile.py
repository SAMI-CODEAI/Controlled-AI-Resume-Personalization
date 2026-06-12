from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.auth import get_current_user
from app.models.user import User
from app.services.latex_compiler import compile_latex

router = APIRouter()

class CompileRequest(BaseModel):
    latex: str

@router.post("")
@router.post("/")
def compile_latex_endpoint(
    payload: CompileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Dynamically compile raw LaTeX code to a PDF on the fly.
    """
    if not payload.latex or not payload.latex.strip():
        raise HTTPException(status_code=400, detail="LaTeX content cannot be empty.")

    try:
        pdf_path = compile_latex(payload.latex)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    if not pdf_path or not pdf_path.endswith('.pdf'):
        # Usually compile_latex either returns path or raises error/returns empty or tex
        raise HTTPException(status_code=500, detail="Compilation failed. See logs.")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="compiled_resume.pdf"
    )
