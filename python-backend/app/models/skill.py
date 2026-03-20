import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)  # e.g., "Programming", "Framework", "Tool"
    proficiency_level = Column(Integer, default=3)  # 1-5 scale
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="skills")
