from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import engine, Base
from app.routers import auth, skills, projects, experiences, achievements, templates, resumes, chat

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="AI Resume Personalization Platform",
    description="Generate job-specific resumes with AI-powered hallucination prevention",
    version="1.0.0",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(skills.router, prefix="/api/skills", tags=["Skills"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(experiences.router, prefix="/api/experiences", tags=["Experiences"])
app.include_router(achievements.router, prefix="/api/achievements", tags=["Achievements"])
app.include_router(templates.router, prefix="/api/templates", tags=["Resume Templates"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["Generated Resumes"])
app.include_router(chat.router, prefix="/api/chat", tags=["AI Refinement Chat"])
