import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ResumeTemplate(Base):
    __tablename__ = "resume_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    latex_content = Column(Text, nullable=False)
    placeholders = Column(Text, nullable=True)  # JSON string of detected placeholders
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="resume_templates")
    generated_resumes = relationship("GeneratedResume", back_populates="template", cascade="all, delete-orphan")
