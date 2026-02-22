import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, Integer
from sqlalchemy.orm import relationship
from app.database import Base


class GeneratedResume(Base):
    __tablename__ = "generated_resumes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id = Column(String, ForeignKey("resume_templates.id", ondelete="SET NULL"), nullable=True)
    job_description = Column(Text, nullable=False)
    latex_output = Column(Text, nullable=False)
    pdf_path = Column(String(500), nullable=True)
    match_score = Column(Float, nullable=True)
    matched_skills = Column(Text, nullable=True)  # JSON
    missing_skills = Column(Text, nullable=True)  # JSON
    metadata_json = Column(Text, nullable=True)  # Full analysis JSON
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="generated_resumes")
    template = relationship("ResumeTemplate", back_populates="generated_resumes")
