import json
import logging
from typing import Dict, Any, List
from app.services.llm_client import call_llm
from app.services.jd_analyzer import analyze_job_description
from app.schemas.schemas import JDAnalysis, MatchScoreBreakdown, ProjectRanking

logger = logging.getLogger(__name__)

ATS_SCORING_PROMPT = """You are an expert ATS (Applicant Tracking System) evaluator. 
Compare the following resume text against the job description analysis and provide a detailed scoring breakdown.

Job Description Analysis:
{jd_analysis}

Resume Text:
{resume_text}

You MUST return valid JSON with exactly these fields:
{{
  "required_skill_match": float (0-100),
  "project_relevance": float (0-100),
  "keyword_alignment": float (0-100),
  "total_score": float (0-100),
  "matched_skills": ["skill1", "skill2", ...],
  "missing_skills": ["skill1", "skill2", ...],
  "improvement_suggestions": ["suggestion1", "suggestion2", ...]
}}

Rules:
- required_skill_match: Percentage of required skills found in the resume.
- project_relevance: How well the projects in the resume align with the JD domain and seniority.
- keyword_alignment: Presence of important industry keywords and methodologies.
- total_score: A weighted average (e.g., 50% skills, 30% projects, 20% keywords).
- matched_skills: Skills from the JD analysis found in the resume.
- missing_skills: Important skills from the JD analysis NOT found in the resume.
- improvement_suggestions: Actionable advice to improve the resume for this specific JD.
"""

def score_resume(resume_text: str, job_description: str) -> MatchScoreBreakdown:
    """
    Score a resume against a job description.
    """
    # 1. Analyze the JD first
    jd_analysis = analyze_job_description(job_description)
    
    # 2. Call LLM to score the resume against the JD analysis
    jd_analysis_json = jd_analysis.model_dump_json()
    
    response = call_llm(
        system_prompt=ATS_SCORING_PROMPT.format(
            jd_analysis=jd_analysis_json,
            resume_text=resume_text[:10000] # Limit resume text to avoid token limits
        ),
        user_prompt="Evaluate the resume against the JD analysis.",
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    
    try:
        data = json.loads(response)
        
        # Note: In a real implementation, we might want to actually rank projects from the DB 
        # or from the parsed resume text. For this plugin, we'll return an empty list of ranked projects
        # or mock them if we can extract them.
        
        return MatchScoreBreakdown(
            required_skill_match=data.get("required_skill_match", 0.0),
            project_relevance=data.get("project_relevance", 0.0),
            keyword_alignment=data.get("keyword_alignment", 0.0),
            total_score=data.get("total_score", 0.0),
            matched_skills=data.get("matched_skills", []),
            missing_skills=data.get("missing_skills", []),
            ranked_projects=[], # Simplified for the plugin
            improvement_suggestions=data.get("improvement_suggestions", [])
        )
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse ATS scoring response: {e}")
        raise ValueError(f"Failed to score resume: {e}")
