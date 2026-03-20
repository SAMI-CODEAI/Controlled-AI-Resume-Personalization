"""
Project Ranker Service.
Ranks user projects by relevance to a job description.
"""
import logging
from typing import List
from app.schemas.schemas import JDAnalysis, ProjectRanking
from app.models.project import Project

logger = logging.getLogger(__name__)


def _normalize(s: str) -> str:
    return s.lower().strip().replace("-", " ").replace("_", " ")


def rank_projects(
    projects: List[Project],
    jd_analysis: JDAnalysis,
    matched_skills: List[str],
) -> List[ProjectRanking]:
    """
    Rank user projects by relevance to the job description.

    Scoring formula:
        score = skill_overlap * 0.5 + domain_weight * 0.3 + impact_weight * 0.2

    Args:
        projects: User's projects from the database
        jd_analysis: Analyzed job description
        matched_skills: Skills that matched between JD and user

    Returns:
        List of ProjectRanking sorted by relevance score (descending)
    """
    rankings = []

    for project in projects:
        project_techs = []
        if project.technologies:
            project_techs = [_normalize(t) for t in project.technologies.split(",")]

        # Skill overlap (0.0 - 1.0)
        all_relevant = set(_normalize(s) for s in matched_skills + jd_analysis.keywords)
        if all_relevant:
            overlap = len(set(project_techs) & all_relevant) / max(len(all_relevant), 1)
        else:
            overlap = 0.0

        # Domain weight (0.0 or 1.0)
        domain_match = 0.0
        if project.domain and jd_analysis.domain:
            if _normalize(project.domain) == _normalize(jd_analysis.domain):
                domain_match = 1.0
            elif _normalize(jd_analysis.domain) in _normalize(project.domain) or \
                 _normalize(project.domain) in _normalize(jd_analysis.domain):
                domain_match = 0.5

        # Impact weight (0.0 - 1.0, based on presence and length of impact description)
        impact_weight = 0.0
        if project.impact:
            impact_weight = min(len(project.impact) / 200.0, 1.0)

        # Final score
        score = (overlap * 0.5) + (domain_match * 0.3) + (impact_weight * 0.2)

        matching_techs = [t for t in project_techs if t in all_relevant]

        rankings.append(ProjectRanking(
            project_id=project.id,
            title=project.title,
            relevance_score=round(score, 3),
            matching_technologies=matching_techs,
        ))

    # Sort by relevance score descending
    rankings.sort(key=lambda r: r.relevance_score, reverse=True)
    return rankings
