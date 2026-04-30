from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.services.document_service import ingest_user_document
from pydantic import BaseModel

router = APIRouter()

class DocumentUploadRequest(BaseModel):
    raw_text: str

@router.post("/", status_code=201)
async def upload_document(
    request: DocumentUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ingest a past performance review or old resume.
    Chunks the text, embed it, and store for RAG capability.
    """
    if not request.raw_text or not request.raw_text.strip():
        raise HTTPException(status_code=400, detail="Text content cannot be empty.")

    chunks_count = ingest_user_document(db, current_user.id, request.raw_text)
    
    return {
        "status": "success",
        "message": f"Document processed and split into {chunks_count} chunks.",
        "chunks": chunks_count
    }
