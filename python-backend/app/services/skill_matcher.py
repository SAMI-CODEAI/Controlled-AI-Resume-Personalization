"""
Skill Matcher Service.
Filters JD-extracted skills against the user's verified skill database.
This is the primary hallucination prevention mechanism.
"""
import logging
from typing import List
from app.schemas.schemas import JDAnalysis, SkillMatchResult

logger = logging.getLogger(__name__)


def _normalize(skill: str) -> str:
    """Normalize a skill name for comparison."""
    return skill.lower().strip().replace("-", " ").replace("_", " ").replace(".", "")


def _fuzzy_match(skill: str, user_skills: List[str]) -> bool:
    """
    Check if a skill matches any user skill with fuzzy matching.
    Handles cases like 'react.js' matching 'react' or 'reactjs'.
    """
    normalized = _normalize(skill)

    for user_skill in user_skills:
        user_normalized = _normalize(user_skill)

        # Exact match
        if normalized == user_normalized:
            return True

        # Substring match (e.g., "react" matches "react.js")
        if normalized in user_normalized or user_normalized in normalized:
            return True

        # Common variations
        variations_map = {
            "js": "javascript",
            "ts": "typescript",
            "py": "python",
            "golang": "go",
            "node": "nodejs",
            "react": "reactjs",
            "vue": "vuejs",
            "angular": "angularjs",
            "postgres": "postgresql",
            "mongo": "mongodb",
            "k8s": "kubernetes",
            "tf": "terraform",
            "aws": "amazon web services",
            "gcp": "google cloud platform",
            "ml": "machine learning",
            "dl": "deep learning",
            "ai": "artificial intelligence",
            "ci/cd": "cicd",
            "ci cd": "cicd",
        }

        for short, full in variations_map.items():
            if (normalized == short and user_normalized == full) or \
               (normalized == full and user_normalized == short):
                return True

    return False


def match_skills(jd_analysis: JDAnalysis, user_skill_names: List[str]) -> SkillMatchResult:
    """
    Match JD skills against user's verified skills.
    Only matched skills will be used in resume generation.

    Args:
        jd_analysis: Extracted JD analysis with required/preferred skills
        user_skill_names: List of skill names from user's database

    Returns:
        SkillMatchResult with matched/missing skills, score, and suggestions
    """
    all_jd_skills = list(set(jd_analysis.required_skills + jd_analysis.preferred_skills))

    matched = []
    missing = []

    for skill in all_jd_skills:
        if _fuzzy_match(skill, user_skill_names):
            matched.append(skill)
        else:
            missing.append(skill)

    # Calculate required skill match percentage
    required_matched = [s for s in jd_analysis.required_skills if _fuzzy_match(s, user_skill_names)]
    required_total = max(len(jd_analysis.required_skills), 1)
    required_match_pct = len(required_matched) / required_total

    # Overall match score
    total = max(len(all_jd_skills), 1)
    match_score = len(matched) / total

    # Generate improvement suggestions
    suggestions = []
    missing_required = [s for s in jd_analysis.required_skills if not _fuzzy_match(s, user_skill_names)]
    if missing_required:
        suggestions.append(
            f"Consider learning these required skills: {', '.join(missing_required[:5])}"
        )
    if match_score < 0.5:
        suggestions.append("Your skill overlap is below 50%. Consider targeting roles more aligned with your expertise.")
    if match_score >= 0.7:
        suggestions.append("Strong match! Focus on highlighting your relevant project experience.")

    return SkillMatchResult(
        matched_skills=matched,
        missing_skills=missing,
        match_score=round(match_score * 100, 1),
        required_match_pct=round(required_match_pct * 100, 1),
        improvement_suggestions=suggestions,
    )
