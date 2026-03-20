"""
Chat Refiner Service.
Handles interactive AI refinement of generated resumes.
Enforces skill constraints and re-validates after every modification.
"""
import json
import logging
import re
from typing import List, Dict, Tuple, Optional
from app.services.llm_client import call_llm_with_history
from app.services.guardrail_validator import validate_resume

logger = logging.getLogger(__name__)

REFINEMENT_SYSTEM_PROMPT = """You are a resume refinement assistant. You help users improve their generated resumes.

CRITICAL RULES:
1. You may ONLY modify content within the existing resume sections.
2. You MUST NOT add any skills, technologies, tools, or experiences that are not in the AUTHORIZED list below.
3. You MUST NOT change the LaTeX template structure — only modify text content.
4. If the user asks you to add an unauthorized skill or technology, REFUSE and explain why.
5. You can improve wording, restructure bullet points, adjust emphasis, and enhance descriptions.
6. Always return the full updated LaTeX content when making changes.

When making changes, return your response as JSON:
{
  "reply": "Your explanation of what you changed",
  "updated_latex": "The full updated LaTeX content (or null if no changes)",
  "changes_made": true/false
}

AUTHORIZED SKILLS (only these may appear in the resume):
{authorized_skills}

Current resume LaTeX:
{current_latex}"""


def clean_llm_json(text: str) -> str:
    """Strip markdown markers and whitespace, or extract JSON block from text."""
    text = text.strip()
    # 1. Try to extract from markdown code blocks
    if "```" in text:
        try:
            # Match the first code block
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                return match.group(1).strip()
        except Exception:
            pass

    # 2. Try to find the first { and last }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace:last_brace+1].strip()

    return text.strip()


def refine_resume(
    message: str,
    current_latex: str,
    authorized_skills: List[str],
    chat_history: List[Dict[str, str]],
) -> Tuple[str, Optional[str], bool, List[str]]:
    """
    Process a refinement request from the user.

    Args:
        message: User's refinement request
        current_latex: Current LaTeX content of the resume
        authorized_skills: List of user's verified skills
        chat_history: Previous chat messages

    Returns:
        Tuple of (reply_text, updated_latex_or_none, validation_passed, validation_errors)
    """
    system_prompt = REFINEMENT_SYSTEM_PROMPT.replace("{authorized_skills}", ", ".join(authorized_skills))
    system_prompt = system_prompt.replace("{current_latex}", current_latex[:3000])

    # Build messages including history
    messages = []
    for msg in chat_history[-10:]:  # Keep last 10 messages for context
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    response = call_llm_with_history(
        system_prompt=system_prompt,
        messages=messages,
        temperature=0.3,
    )

    # Parse the response
    try:
        cleaned_response = clean_llm_json(response)
        data = json.loads(cleaned_response)
        reply = data.get("reply", response)
        updated_latex = data.get("updated_latex")
        changes_made = data.get("changes_made", False)
    except Exception:
        # If response isn't JSON, treat it as a plain text reply
        return response, None, True, []

    # If changes were made, validate the updated content
    validation_errors = []
    validation_passed = True

    if updated_latex and changes_made:
        is_valid, violations = validate_resume(updated_latex, authorized_skills, strict=True)
        if not is_valid:
            validation_passed = False
            validation_errors = violations
            reply += f"\n\n⚠️ WARNING: The changes were rejected because they contain unauthorized skills: {', '.join(violations)}. The resume was not updated."
            updated_latex = None  # Reject the update

    return reply, updated_latex, validation_passed, validation_errors
