from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import engine, Base
from app.routers import auth, skills, projects, experiences, achievements, templates, resumes, chat, agent_traces, documents, compile, ats

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
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(skills.router, prefix="/api/v1/skills", tags=["Skills"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(experiences.router, prefix="/api/v1/experiences", tags=["Experiences"])
app.include_router(achievements.router, prefix="/api/v1/achievements", tags=["Achievements"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["Resume Templates"])
app.include_router(resumes.router, prefix="/api/v1/resumes", tags=["Generated Resumes"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["AI Refinement Chat"])
app.include_router(agent_traces.router, prefix="/api/v1/resumes", tags=["Agent Traces"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["User Reference Documents"])
app.include_router(compile.router, prefix="/api/v1/compile", tags=["LaTeX Compilation"])
app.include_router(ats.router, prefix="/api/v1", tags=["ATS Resume Scorer"])
