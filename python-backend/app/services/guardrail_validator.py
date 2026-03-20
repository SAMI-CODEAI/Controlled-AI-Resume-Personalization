"""
Guardrail Validator Service.
Programmatically validates that generated resume content contains ONLY authorized skills.
This is the final line of defense against AI hallucination.
"""
import re
import logging
from typing import List, Tuple, Set

logger = logging.getLogger(__name__)


def _normalize(skill: str) -> str:
    """Normalize a skill for comparison."""
    return skill.lower().strip().replace("-", " ").replace("_", " ").replace(".", "").replace(",", "")


def _extract_technologies_from_latex(latex_content: str) -> Set[str]:
    """
    Extract technology/skill mentions from LaTeX content.
    Uses multiple strategies to catch different formatting patterns.
    """
    extracted = set()

    # Remove LaTeX commands but keep their text content
    clean = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', latex_content)
    clean = re.sub(r'\\[a-zA-Z]+', ' ', clean)
    clean = re.sub(r'[{}\\%$&~^]', ' ', clean)

    # Strategy 1: Extract from common skill listing patterns
    # Pattern: "Skills: Python, Java, React" or "Technologies: ..."
    skill_section_pattern = re.compile(
        r'(?:skills?|technologies?|tools?|frameworks?|languages?|platforms?)\s*[:\-|]\s*([^\n]+)',
        re.IGNORECASE
    )
    for match in skill_section_pattern.findall(clean):
        items = re.split(r'[,;|/]', match)
        for item in items:
            cleaned = item.strip()
            if cleaned and len(cleaned) > 1 and len(cleaned) < 50:
                extracted.add(_normalize(cleaned))

    # Strategy 2: Extract from itemized lists
    item_pattern = re.compile(r'\\?item\s+(.+?)(?:\n|$)')
    for match in item_pattern.findall(latex_content):
        clean_match = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', match)
        clean_match = re.sub(r'[{}\\]', '', clean_match).strip()
        if clean_match and len(clean_match) < 50:
            # Split by common delimiters
            for part in re.split(r'[,;|]', clean_match):
                part = part.strip()
                if part and len(part) > 1:
                    extracted.add(_normalize(part))

    # Strategy 3: Extract bold/emphasized terms (often skills)
    bold_pattern = re.compile(r'\\textbf\{([^}]+)\}')
    for match in bold_pattern.findall(latex_content):
        extracted.add(_normalize(match))

    return extracted


# Common English words to exclude from skill matching
_COMMON_WORDS = {
    "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "is", "are", "was", "were", "be", "been", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "shall", "can", "need", "must", "it", "its", "this", "that", "these", "those",
    "i", "me", "my", "we", "us", "our", "you", "your", "he", "him", "his",
    "she", "her", "they", "them", "their", "what", "which", "who", "whom",
    "not", "no", "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "than", "too", "very", "just", "also", "about", "up", "out",
    "new", "used", "using", "developed", "built", "created", "designed", "implemented",
    "managed", "led", "worked", "experience", "experienced", "proficient", "strong",
    "team", "project", "system", "application", "development", "engineering",
    "software", "data", "web", "cloud", "server", "client", "user", "business",
    "years", "year", "over", "across", "multiple", "various", "key", "core",
    "professional", "technical", "including", "across", "ensured", "within",
    "collaborated", "distributed", "optimized", "integrated", "facilitated",
    "maintained", "performed", "involved", "provided", "high", "performance",
    "quality", "production", "services", "solutions", "features", "delivery",
    "successful", "driven", "focused", "based", "related", "associated",
}


def validate_resume(
    generated_latex: str,
    authorized_terms: List[str],
    strict: bool = True,
) -> Tuple[bool, List[str]]:
    """
    Validate that generated resume content only contains authorized professional entities.

    Args:
        generated_latex: The generated LaTeX resume content
        authorized_terms: List of all skills, project titles, and company names from user's database
        strict: If True, reject on ANY unauthorized skill
    """
    extracted = _extract_technologies_from_latex(generated_latex)
    normalized_auth_terms = {_normalize(s) for s in authorized_terms}

    violations = []

    for tech in extracted:
        # Skip common words
        if tech in _COMMON_WORDS:
            continue
        # Skip very short or very long strings
        if len(tech) < 2 or len(tech) > 60:
            continue

        # Check if this technology/entity is in user's authorized set
        is_authorized = False
        
        for auth_term in normalized_auth_terms:
            if tech == auth_term:
                is_authorized = True
                break
            # Allow "React.js" to match "React" or vice-versa
            if tech in auth_term or auth_term in tech:
                # But only if it's not a common word substring (e.g. "and" in "Android")
                if len(tech) > 3 or tech == auth_term:
                    is_authorized = True
                    break
        
        # Heuristic: if a "tech" is multiple words and none of them are in authorized_terms,
        # it's likely a sentence fragment we extracted by mistake.
        if not is_authorized and " " in tech:
            words = tech.split()
            if any(w in normalized_auth_terms for w in words):
                is_authorized = True
        
        if not is_authorized:
            violations.append(tech)

    is_valid = len(violations) == 0 if strict else len(violations) <= 3

    if violations:
        logger.warning(f"Guardrail validation found {len(violations)} violations: {violations}")

    return is_valid, violations
