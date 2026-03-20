"""
JD (Job Description) Analyzer Service.
Extracts structured information from job descriptions using LLM.
"""
import json
import logging
from typing import Dict, Any
from app.services.llm_client import call_llm
from app.schemas.schemas import JDAnalysis

logger = logging.getLogger(__name__)

JD_ANALYSIS_PROMPT = """You are a job description analyzer. Extract structured information from the given job description.

You MUST return valid JSON with exactly these fields:
{
  "required_skills": ["skill1", "skill2", ...],
  "preferred_skills": ["skill1", "skill2", ...],
  "keywords": ["keyword1", "keyword2", ...],
  "domain": "string describing the domain (e.g., Web Development, Machine Learning, DevOps)",
  "seniority": "string (Junior, Mid-Level, Senior, Lead, Principal, Staff)"
}

Rules:
- required_skills: Skills explicitly stated as required or mandatory
- preferred_skills: Skills listed as nice-to-have, preferred, or bonus
- keywords: Important domain terms, methodologies, and technologies mentioned
- domain: The primary technical domain of the role
- seniority: Inferred seniority level from title, years of experience, and responsibilities
- Normalize skill names to lowercase
- Remove duplicates between required and preferred
- Be thorough but precise — only extract what is explicitly mentioned"""


def analyze_job_description(job_description: str) -> JDAnalysis:
    """
    Analyze a job description and extract structured data.

    Args:
        job_description: Raw job description text

    Returns:
        JDAnalysis with extracted skills, keywords, domain, and seniority
    """
    response = call_llm(
        system_prompt=JD_ANALYSIS_PROMPT,
        user_prompt=f"Analyze this job description:\n\n{job_description}",
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(response)
        return JDAnalysis(
            required_skills=[s.lower().strip() for s in data.get("required_skills", [])],
            preferred_skills=[s.lower().strip() for s in data.get("preferred_skills", [])],
            keywords=[k.lower().strip() for k in data.get("keywords", [])],
            domain=data.get("domain", "General"),
            seniority=data.get("seniority", "Mid-Level"),
        )
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse JD analysis response: {e}")
        raise ValueError(f"Failed to analyze job description: {e}")
