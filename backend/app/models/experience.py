import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Date, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Experience(Base):
    __tablename__ = "experiences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    technologies = Column(Text, nullable=True)  # Comma-separated
    location = Column(String(255), nullable=True)
    is_current = Column(Boolean, default=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="experiences")
