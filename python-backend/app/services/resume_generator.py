"""
Resume Generator Service.
Fills LaTeX template placeholders with AI-generated content using ONLY verified user data.
NEVER regenerates the full template — only modifies %%PLACEHOLDER%% sections.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from app.services.llm_client import call_llm
from app.models.project import Project
from app.models.experience import Experience

logger = logging.getLogger(__name__)

RESUME_GENERATION_PROMPT = """You are a professional resume writer. Your task is to generate content for specific resume placeholders.

CRITICAL RULES:
1. You MUST ONLY use the skills, projects, and experiences provided below.
2. You MUST NOT invent, hallucinate, or add any skills, technologies, tools, or experiences not listed.
3. You MUST NOT add any company names, job titles, or project names not provided.
4. Output valid LaTeX content that can be directly inserted into a template.
5. Use professional, concise language appropriate for resumes.
6. Tailor the content to match the job description while ONLY using provided data.

You MUST return valid JSON with these keys (each value is a LaTeX string):
{
  "summary": "LaTeX content for professional summary",
  "skills": "LaTeX content for skills section",
  "projects": "LaTeX content for projects section",
  "experiences": "LaTeX content for experience section"
}

IMPORTANT: Escape LaTeX special characters properly. Use \\\\textbf, \\\\item, etc. 
You MUST close every environment you open (e.g., if you use \\\\begin{itemize}, you MUST end it with \\\\end{itemize}). Ensure nested environments are also balanced."""


def validate_latex_structure(latex_text: str) -> List[str]:
    """
    Checks for unbalanced LaTeX environments (\begin{...} vs \end{...}).
    Returns a list of error messages.
    """
    import re
    errors = []
    stack = []
    
    # Find all \begin{env} and \end{env} tags
    pattern = re.compile(r"\\(begin|end)\{([^}]+)\}")
    matches = pattern.finditer(latex_text)
    
    for match in matches:
        tag_type = match.group(1)
        env_name = match.group(2)
        
        if tag_type == "begin":
            stack.append((env_name, match.start()))
        else:
            if not stack:
                errors.append(f"Found \\end{{{env_name}}} without matching \\begin")
            else:
                last_begin, _ = stack.pop()
                if last_begin != env_name:
                    errors.append(f"Environment mismatch: \\begin{{{last_begin}}} ended by \\end{{{env_name}}}")
    
    while stack:
        env_name, _ = stack.pop()
        errors.append(f"Environment \\begin{{{env_name}}} is never closed with \\end{{{env_name}}}")
        
    return errors


def generate_resume_content(
    job_description: str,
    matched_skills: List[str],
    ranked_projects: List[Dict[str, Any]],
    experiences: List[Experience],
    domain: str,
    seniority: str,
) -> Dict[str, str]:
    """
    Generate resume placeholder content using only verified user data.

    Args:
        job_description: The target job description
        matched_skills: ONLY skills verified from user's database
        ranked_projects: Projects ranked by relevance
        experiences: User's work experiences
        domain: Target job domain
        seniority: Target seniority level

    Returns:
        Dict mapping placeholder names to LaTeX content
    """
    # Build context from verified data only
    skills_text = ", ".join(matched_skills) if matched_skills else "No matching skills"

    projects_text = ""
    for i, proj in enumerate(ranked_projects[:5], 1):
        projects_text += f"\n{i}. {proj['title']}: {proj['description']}"
        if proj.get('technologies'):
            projects_text += f" (Technologies: {proj['technologies']})"
        if proj.get('impact'):
            projects_text += f" Impact: {proj['impact']}"

    experiences_text = ""
    for exp in experiences:
        experiences_text += f"\n- {exp.role} at {exp.company}: {exp.description}"
        if exp.technologies:
            experiences_text += f" (Technologies: {exp.technologies})"

    user_prompt = f"""Job Description:
{job_description}

Domain: {domain}
Seniority: {seniority}

VERIFIED SKILLS (use ONLY these):
{skills_text}

VERIFIED PROJECTS (use ONLY these):
{projects_text}

VERIFIED EXPERIENCES (use ONLY these):
{experiences_text}

Generate LaTeX content for each placeholder. Remember: use ONLY the data above, do not add anything else."""

    response = call_llm(
        system_prompt=RESUME_GENERATION_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    try:
        content = json.loads(response)
        # Ensure all expected keys exist
        for key in ["summary", "skills", "projects", "experiences"]:
            if key not in content:
                content[key] = ""
            
            # Structural validation
            struct_errors = validate_latex_structure(content[key])
            if struct_errors:
                logger.warning(f"LaTeX structural errors in section '{key}': {struct_errors}")
                # We could attempt a basic fix here, but for now, we'll let it be and rely 
                # on the retry logic in the router if compilation fails.
                # Or we can append missing tags if we're feeling brave.
                for err in struct_errors:
                    if "never closed" in err:
                        env = err.split("\\begin{")[1].split("}")[0]
                        content[key] += f"\n\\end{{{env}}}"

        return content
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse resume generation response: {e}")
        raise ValueError(f"Resume generation failed: {e}")


def fill_template(template_latex: str, content: Dict[str, str], user: Optional[Any] = None) -> str:
    """
    Replace markers in the template with generated content and user info.
    Supports %%KEY%%, {{key}}, and [[key]] styles (case-insensitive).
    """
    result = template_latex
    
    # Standardize markers
    full_content = {k.lower(): v for k, v in content.items()}
    if user:
        full_content.update({
            "full_name": user.full_name,
            "email": user.email,
        })

    # Loop over all potential keys found in the template using regex for robustness
    import re
    
    # 1. Replace {{key}}, [[key]], %%key%% styles (case-insensitive)
    for key, value in full_content.items():
        # Build patterns that match the key case-insensitively within markers
        patterns = [
            (rf"{{{{\s*{re.escape(key)}\s*}}}}", str(value)),
            (rf"\[\[\s*{re.escape(key)}\s*\]\]", str(value)),
            (rf"%%\s*{re.escape(key)}\s*%%", str(value)),
        ]
        
        for pattern, replacement in patterns:
            result = re.sub(pattern, lambda m: replacement, result, flags=re.IGNORECASE)
    
    # Safety check: Ensure no content is appended after \end{document}
    if "\\end{document}" in result:
        parts = result.split("\\end{document}")
        result = parts[0] + "\\end{document}"
        
    return result
