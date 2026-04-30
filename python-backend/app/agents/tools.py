"""
Formal Agent Tool Registry.

Each tool is a plain Python callable with a structured docstring and typed
signature. Tools are the atomic units of capability that agent nodes invoke.
This pattern mirrors LangChain's @tool decorator semantics without requiring
the dependency — keeping coupling low while preserving the conceptual clarity
of "agents use tools."

By centralising service calls here we get:
  1. A single import path referenced in both nodes.py and tests.
  2. Natural seam for mocking in unit tests.
  3. Self-documenting interface for each agentic capability.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool: Analyze Job Description
# ---------------------------------------------------------------------------

def analyze_jd_tool(job_description: str) -> Dict[str, Any]:
    """
    Tool: JD Analyst
    Parse a raw job description and extract structured requirements.
    Returns a dict with keys: domain, seniority, keywords, required_skills,
    nice_to_have_skills, responsibilities.
    """
    from app.services.jd_analyzer import analyze_job_description
    result = analyze_job_description(job_description)
    return result.model_dump()


# ---------------------------------------------------------------------------
# Tool: Match Skills
# ---------------------------------------------------------------------------

def match_skills_tool(
    jd_analysis: Dict[str, Any],
    user_skill_names: List[str],
) -> Dict[str, Any]:
    """
    Tool: Skill Matcher
    Compare JD requirements against the user's verified skill database.
    Returns a dict with: matched_skills, missing_skills, required_match_pct,
    improvement_suggestions.
    Hallucination prevention: only skills in user_skill_names can appear.
    """
    from app.services.skill_matcher import match_skills
    from app.services.jd_analyzer import JDAnalysis
    jd = JDAnalysis(**jd_analysis)
    result = match_skills(jd, user_skill_names)
    return result.model_dump()


# ---------------------------------------------------------------------------
# Tool: Rank Projects
# ---------------------------------------------------------------------------

def rank_projects_tool(
    user_projects: List[Any],
    jd_analysis: Dict[str, Any],
    matched_skills: List[str],
) -> List[Dict[str, Any]]:
    """
    Tool: Project Ranker
    Score each user project by relevance to the job description.
    Returns a list of ProjectRanking dicts ordered by relevance_score descending.
    """
    from app.services.project_ranker import rank_projects
    from app.services.jd_analyzer import JDAnalysis
    jd = JDAnalysis(**jd_analysis)
    rankings = rank_projects(user_projects, jd, matched_skills)
    return [r.model_dump() for r in rankings]


# ---------------------------------------------------------------------------
# Tool: Generate Resume Content
# ---------------------------------------------------------------------------

def generate_content_tool(
    job_description: str,
    matched_skills: List[str],
    ranked_project_data: List[Dict[str, Any]],
    experiences: List[Any],
    domain: str,
    seniority: str,
    repair_feedback: Optional[str] = None,
    historical_context: Optional[List[str]] = None,
) -> Dict[str, str]:
    """
    Tool: Content Writer
    Generate LaTeX placeholder content for summary, skills, projects, experiences.
    If repair_feedback is provided, it is injected into the prompt so the LLM
    can self-correct on a retry cycle.
    Returns: {summary, skills, projects, experiences} — each value is LaTeX.
    """
    from app.services.resume_generator import generate_resume_content, RESUME_GENERATION_PROMPT
    from app.services.llm_client import call_llm
    import json

    if repair_feedback:
        # Inject repair context into the system prompt for self-healing
        augmented_system = (
            RESUME_GENERATION_PROMPT
            + f"\n\nPREVIOUS ATTEMPT FAILED. REPAIR REQUIRED:\n{repair_feedback}\n"
            "Fix ALL issues listed above. Do not repeat the same mistakes."
        )
        if historical_context:
            augmented_system += "\n\nHISTORICAL STYLE & METRICS:\n" + "\n".join(historical_context) + "\nIncorporate the exact historical writing style and impact metrics from the text above."

        skills_text = ", ".join(matched_skills) if matched_skills else "No matching skills"
        projects_text = ""
        for i, proj in enumerate(ranked_project_data[:5], 1):
            projects_text += f"\n{i}. {proj['title']}: {proj['description']}"
            if proj.get("technologies"):
                projects_text += f" (Technologies: {proj['technologies']})"
        experiences_text = ""
        for exp in experiences:
            if hasattr(exp, "role"):
                experiences_text += f"\n- {exp.role} at {exp.company}: {exp.description}"
            else:
                experiences_text += f"\n- {exp.get('role','Role')} at {exp.get('company','Company')}"

        user_prompt = (
            f"Job Description:\n{job_description}\n\nDomain: {domain}\nSeniority: {seniority}\n\n"
            f"VERIFIED SKILLS: {skills_text}\nVERIFIED PROJECTS: {projects_text}\n"
            f"VERIFIED EXPERIENCES: {experiences_text}\n\n"
            "Generate corrected LaTeX content for each placeholder."
        )
        response = call_llm(
            system_prompt=augmented_system,
            user_prompt=user_prompt,
            temperature=0.15,
            response_format={"type": "json_object"},
        )
        content = json.loads(response)
        for key in ["summary", "skills", "projects", "experiences"]:
            if key not in content:
                content[key] = ""
        return content

    return generate_resume_content(
        job_description=job_description,
        matched_skills=matched_skills,
        ranked_projects=ranked_project_data,
        experiences=experiences,
        domain=domain,
        seniority=seniority,
        historical_context=historical_context or [],
    )


# ---------------------------------------------------------------------------
# Tool: Fill Template
# ---------------------------------------------------------------------------

def fill_template_tool(
    template_latex: str,
    content: Dict[str, str],
    user: Optional[Any] = None,
) -> str:
    """
    Tool: Template Filler
    Replace %%PLACEHOLDER%% markers in the LaTeX template with generated content.
    Returns the complete filled LaTeX document string.
    """
    from app.services.resume_generator import fill_template
    return fill_template(template_latex, content, user)


# ---------------------------------------------------------------------------
# Tool: Validate LaTeX Structure
# ---------------------------------------------------------------------------

def validate_latex_tool(content_dict: Dict[str, str]) -> List[str]:
    """
    Tool: LaTeX Critic
    Check each resume section for unbalanced \\begin{} / \\end{} environments.
    Returns a flat list of error strings, empty if structure is valid.
    """
    from app.services.resume_generator import validate_latex_structure
    all_errors = []
    for section, latex in content_dict.items():
        errors = validate_latex_structure(latex)
        for e in errors:
            all_errors.append(f"[{section}] {e}")
    return all_errors


# ---------------------------------------------------------------------------
# Tool: Validate Guardrails
# ---------------------------------------------------------------------------

def validate_guardrails_tool(
    latex: str,
    authorized_terms: List[str],
    strict: bool = True,
) -> Tuple[bool, List[str]]:
    """
    Tool: Guardrail Critic
    Verify that no unauthorized skills, companies, or entities appear in the resume.
    This is the primary anti-hallucination defence.
    Returns (is_valid, violations_list).
    """
    from app.services.guardrail_validator import validate_resume
    return validate_resume(latex, authorized_terms, strict=strict)


# ---------------------------------------------------------------------------
# Tool: Compile LaTeX
# ---------------------------------------------------------------------------

def compile_latex_tool(latex_content: str) -> Optional[str]:
    """
    Tool: Compiler Agent
    Compile the final LaTeX document to PDF via Docker sandbox or local pdflatex.
    Returns the PDF file path on success, or None if compilation is unavailable.
    """
    try:
        from app.services.latex_compiler import compile_latex
        return compile_latex(latex_content)
    except Exception as e:
        logger.warning(f"[Compiler Agent] LaTeX compilation failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Tool: Reflection Scoring
# ---------------------------------------------------------------------------

def reflection_tool(
    filled_latex: str,
    job_description: str,
    matched_skills: List[str],
) -> Tuple[int, str]:
    """
    Tool: Reflection Agent
    Ask the LLM to critically evaluate the generated resume against the job
    description and return a quality score (1-10) plus a critique string.
    Score < 6 means the resume should be repaired and regenerated.
    Returns (score: int, critique: str).
    """
    from app.services.llm_client import call_llm
    import json
    import re

    system_prompt = """You are a senior technical recruiter from a FAANG company evaluating resumes.
Score the provided resume on a scale of 1-10 for the given job description.

Evaluation criteria:
- Relevance to job requirements (30%)
- Technical depth and specificity (25%)
- Quantifiable impact/achievements (20%)
- LaTeX formatting quality (15%)
- Professional language (10%)

Return ONLY JSON:
{
  "score": <integer 1-10>,
  "critique": "<2-3 sentence critique identifying specific weaknesses>",
  "strengths": "<1-2 sentence summary of strengths>"
}"""

    # Truncate for token efficiency
    latex_preview = filled_latex[:2000]
    skills_text = ", ".join(matched_skills[:20])

    user_prompt = (
        f"Job Description:\n{job_description[:1000]}\n\n"
        f"Matched Skills: {skills_text}\n\n"
        f"Resume LaTeX (truncated):\n{latex_preview}\n\n"
        "Score this resume and provide critique."
    )

    try:
        response = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        data = json.loads(response)
        score = int(data.get("score", 7))
        score = max(1, min(10, score))
        critique = data.get("critique", "No critique provided.")
        strengths = data.get("strengths", "")
        full_critique = f"Score: {score}/10\nStrengths: {strengths}\nWeaknesses: {critique}"
        return score, full_critique
    except Exception as e:
        logger.warning(f"[Reflection Agent] Scoring failed: {e}. Defaulting to score=7.")
        return 7, "Reflection scoring unavailable — defaulting to acceptable quality."
