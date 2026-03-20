"""
Edge case tests for the resume platform.
"""
import pytest
from app.services.skill_matcher import match_skills
from app.services.project_ranker import rank_projects
from app.services.guardrail_validator import validate_resume
from app.services.resume_generator import fill_template
from app.schemas.schemas import JDAnalysis
from unittest.mock import MagicMock


class TestEdgeCases:
    def test_empty_job_description_skills(self):
        """JD with no extractable skills."""
        jd = JDAnalysis(
            required_skills=[],
            preferred_skills=[],
            keywords=[],
            domain="Unknown",
            seniority="Unknown",
        )
        result = match_skills(jd, ["Python", "Java"])
        assert result.match_score == 0.0

    def test_single_skill_match(self):
        """User has exactly one matching skill."""
        jd = JDAnalysis(
            required_skills=["python"],
            preferred_skills=[],
            keywords=[],
            domain="Web",
            seniority="Junior",
        )
        result = match_skills(jd, ["Python"])
        assert result.match_score == 100.0
        assert len(result.matched_skills) == 1

    def test_duplicate_skills_in_jd(self):
        """JD lists the same skill in both required and preferred."""
        jd = JDAnalysis(
            required_skills=["python", "python"],
            preferred_skills=["python"],
            keywords=[],
            domain="Web",
            seniority="Junior",
        )
        result = match_skills(jd, ["Python"])
        # Should deduplicate
        assert result.match_score == 100.0

    def test_no_projects_ranking(self):
        """Ranking with no projects."""
        jd = JDAnalysis(
            required_skills=["python"],
            preferred_skills=[],
            keywords=["web"],
            domain="Web",
            seniority="Senior",
        )
        rankings = rank_projects([], jd, ["python"])
        assert len(rankings) == 0

    def test_project_without_technologies(self):
        """Project with no technologies field."""
        mock_project = MagicMock()
        mock_project.id = "proj-1"
        mock_project.title = "My Project"
        mock_project.technologies = None
        mock_project.domain = "Web"
        mock_project.impact = "Big impact"

        jd = JDAnalysis(
            required_skills=["python"],
            preferred_skills=[],
            keywords=["web"],
            domain="Web",
            seniority="Senior",
        )
        rankings = rank_projects([mock_project], jd, ["python"])
        assert len(rankings) == 1

    def test_latex_with_special_characters(self):
        """LaTeX template with special characters in content."""
        template = r"""
\section{Skills}
%%SKILLS%%
\section{Summary}
%%SUMMARY%%
"""
        content = {
            "SKILLS": r"Python \& JavaScript \% Web",
            "SUMMARY": r"Developer with 5+ years \$ experience",
        }
        result = fill_template(template, content)
        assert r"Python \& JavaScript" in result
        assert "%%SKILLS%%" not in result

    def test_very_long_skill_list(self):
        """Handle a very large number of skills."""
        jd = JDAnalysis(
            required_skills=[f"skill_{i}" for i in range(100)],
            preferred_skills=[],
            keywords=[],
            domain="Web",
            seniority="Senior",
        )
        user_skills = [f"Skill_{i}" for i in range(50)]
        result = match_skills(jd, user_skills)
        assert result.match_score == 50.0

    def test_unicode_in_skills(self):
        """Skills with unicode characters."""
        jd = JDAnalysis(
            required_skills=["c++", "c#"],
            preferred_skills=[],
            keywords=[],
            domain="Systems",
            seniority="Senior",
        )
        user_skills = ["C++", "C#"]
        result = match_skills(jd, user_skills)
        assert len(result.matched_skills) >= 1

    def test_guardrail_with_latex_commands(self):
        """Ensure LaTeX commands don't get mistaken for skills."""
        latex = r"""
        \documentclass{article}
        \usepackage{enumitem}
        \begin{document}
        \section{Skills}
        Technologies: Python
        \end{document}
        """
        is_valid, violations = validate_resume(latex, ["Python"])
        # LaTeX commands like 'enumitem' should not be flagged
        assert "enumitem" not in violations
