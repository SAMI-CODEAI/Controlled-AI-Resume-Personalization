"""
Agent Traces Router.

Exposes the per-resume agent execution trace stored in metadata_json.
This allows the frontend to display the multi-agent reasoning chain,
making the agentic system's decision-making transparent to users.

Endpoint:
  GET /resumes/{resume_id}/trace
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from typing import List, Optional, Any, Dict

from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.generated_resume import GeneratedResume
from app.auth.auth import get_current_user

router = APIRouter()


class AgentTraceEventResponse(BaseModel):
    agent: str
    status: str
    duration_ms: int
    details: str
    errors: List[str] = []


class AgentTraceResponse(BaseModel):
    resume_id: str
    version: int
    total_agents: int
    repair_cycles: int
    reflection_score: Optional[int]
    final_status: Optional[str]
    agent_memory_snapshot: Optional[Dict[str, Any]]
    trace: List[AgentTraceEventResponse]


@router.get("/{resume_id}/trace", response_model=AgentTraceResponse)
def get_agent_trace(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve the full multi-agent execution trace for a generated resume.

    Returns each agent's name, status, wall-clock duration, what it did,
    and any errors it encountered — providing full transparency into how
    the agentic pipeline produced this resume.
    """
    resume = db.query(GeneratedResume).filter(
        GeneratedResume.id == resume_id,
        GeneratedResume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.metadata_json:
        raise HTTPException(status_code=404, detail="Agent trace not available for this resume")

    metadata = json.loads(resume.metadata_json)
    raw_trace = metadata.get("agent_trace", [])

    if not raw_trace:
        raise HTTPException(
            status_code=404,
            detail=(
                "No agent trace found. This resume may have been generated before "
                "the multi-agent system was deployed."
            ),
        )

    trace_events = [
        AgentTraceEventResponse(
            agent=e.get("agent", "Unknown Agent"),
            status=e.get("status", "unknown"),
            duration_ms=e.get("duration_ms", 0),
            details=e.get("details", ""),
            errors=e.get("errors", []),
        )
        for e in raw_trace
    ]

    return AgentTraceResponse(
        resume_id=resume_id,
        version=resume.version,
        total_agents=len(trace_events),
        repair_cycles=metadata.get("repair_cycles", 0),
        reflection_score=metadata.get("reflection_score"),
        final_status="success" if not any(e.status == "failed" for e in trace_events) else "partial",
        agent_memory_snapshot=metadata.get("agent_memory_snapshot"),
        trace=trace_events,
    )
