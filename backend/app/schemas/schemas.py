from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date


# ─── User Schemas ───────────────────────────────────────────────
class UserCreate(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., max_length=255)


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ─── Skill Schemas ──────────────────────────────────────────────
class SkillCreate(BaseModel):
    name: str = Field(..., max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    proficiency_level: int = Field(3, ge=1, le=5)


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    proficiency_level: Optional[int] = Field(None, ge=1, le=5)


class SkillResponse(BaseModel):
    id: str
    name: str
    category: Optional[str]
    proficiency_level: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Project Schemas ────────────────────────────────────────────
class ProjectCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    technologies: Optional[str] = None
    impact: Optional[str] = None
    domain: Optional[str] = Field(None, max_length=100)
    url: Optional[str] = Field(None, max_length=500)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    technologies: Optional[str] = None
    impact: Optional[str] = None
    domain: Optional[str] = Field(None, max_length=100)
    url: Optional[str] = Field(None, max_length=500)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectResponse(BaseModel):
    id: str
    title: str
    description: str
    technologies: Optional[str]
    impact: Optional[str]
    domain: Optional[str]
    url: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Experience Schemas ─────────────────────────────────────────
class ExperienceCreate(BaseModel):
    company: str = Field(..., max_length=255)
    role: str = Field(..., max_length=255)
    description: str
    technologies: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    is_current: bool = False
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ExperienceUpdate(BaseModel):
    company: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    technologies: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    is_current: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ExperienceResponse(BaseModel):
    id: str
    company: str
    role: str
    description: str
    technologies: Optional[str]
    location: Optional[str]
    is_current: bool
    start_date: Optional[date]
    end_date: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Achievement Schemas ────────────────────────────────────────
class AchievementCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    date: Optional[date] = None


class AchievementUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    date: Optional[date] = None


class AchievementResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    date: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Resume Template Schemas ────────────────────────────────────
class TemplateCreate(BaseModel):
    name: str = Field(..., max_length=255)
    latex_content: str


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    latex_content: Optional[str] = None


class TemplateResponse(BaseModel):
    id: str
    name: str
    latex_content: str
    placeholders: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Generated Resume Schemas ───────────────────────────────────
class ResumeGenerateRequest(BaseModel):
    template_id: str
    job_description: str


class ResumeResponse(BaseModel):
    id: str
    template_id: Optional[str]
    job_description: str
    latex_output: str
    pdf_path: Optional[str]
    match_score: Optional[float]
    matched_skills: Optional[str]
    missing_skills: Optional[str]
    metadata_json: Optional[str]
    version: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── JD Analysis Schemas ────────────────────────────────────────
class JDAnalysis(BaseModel):
    required_skills: List[str]
    preferred_skills: List[str]
    keywords: List[str]
    domain: str
    seniority: str


class SkillMatchResult(BaseModel):
    matched_skills: List[str]
    missing_skills: List[str]
    match_score: float
    required_match_pct: float
    improvement_suggestions: List[str]


class ProjectRanking(BaseModel):
    project_id: str
    title: str
    relevance_score: float
    matching_technologies: List[str]


class MatchScoreBreakdown(BaseModel):
    required_skill_match: float
    project_relevance: float
    keyword_alignment: float
    total_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    ranked_projects: List[ProjectRanking]
    improvement_suggestions: List[str]


# ─── Chat Schemas ───────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    resume_id: str
    message: str
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    updated_latex: Optional[str] = None
    validation_passed: bool
    validation_errors: List[str] = []
