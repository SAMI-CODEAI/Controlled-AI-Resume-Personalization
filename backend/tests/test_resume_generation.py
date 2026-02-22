"""
Integration tests for the resume generation pipeline.
Tests the end-to-end flow without LLM calls (mocked).
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from app.services.resume_generator import fill_template, generate_resume_content
from app.services.guardrail_validator import validate_resume


class TestFillTemplate:
    def test_fills_all_placeholders(self):
        template = r"""
\documentclass{article}
\begin{document}
\section{Summary}
%%SUMMARY%%
\section{Skills}
%%SKILLS%%
\section{Projects}
%%PROJECTS%%
\section{Experience}
%%EXPERIENCE%%
\end{document}
"""
        content = {
            "SUMMARY": "Experienced Python developer",
            "SKILLS": "Python, FastAPI, React",
            "PROJECTS": r"\item AI Resume Builder - Built with Python",
            "EXPERIENCE": r"\item Senior Engineer at Tech Corp",
        }
        result = fill_template(template, content)
        assert "%%SUMMARY%%" not in result
        assert "%%SKILLS%%" not in result
        assert "%%PROJECTS%%" not in result
        assert "%%EXPERIENCE%%" not in result
        assert "Experienced Python developer" in result
        assert "Python, FastAPI, React" in result

    def test_preserves_template_structure(self):
        template = r"""
\documentclass{article}
\usepackage{geometry}
\begin{document}
\section{Summary}
%%SUMMARY%%
\end{document}
"""
        content = {"SUMMARY": "Test summary"}
        result = fill_template(template, content)
        assert r"\documentclass{article}" in result
        assert r"\usepackage{geometry}" in result
        assert r"\begin{document}" in result
        assert r"\end{document}" in result

    def test_handles_missing_placeholder(self):
        template = r"%%SUMMARY%% and %%CUSTOM%%"
        content = {"SUMMARY": "Test"}
        result = fill_template(template, content)
        assert "Test" in result
        assert "%%CUSTOM%%" in result  # Unmatched placeholder stays

    def test_handles_empty_content(self):
        template = r"%%SUMMARY%%"
        content = {"SUMMARY": ""}
        result = fill_template(template, content)
        assert result == ""


class TestEndToEndValidation:
    """Test the full pipeline: generate → fill → validate."""

    def test_valid_pipeline(self):
        """Test that a properly generated resume passes validation."""
        template = r"""
\section{Skills}
%%SKILLS%%
\section{Summary}
%%SUMMARY%%
"""
        user_skills = ["Python", "FastAPI", "React"]
        content = {
            "SKILLS": r"Technologies: Python, FastAPI, React",
            "SUMMARY": r"Full-stack developer with expertise in Python and React",
        }

        filled = fill_template(template, content)
        is_valid, violations = validate_resume(filled, user_skills)
        assert is_valid is True

    def test_hallucinated_skill_caught(self):
        """Test that hallucinated skills are caught in the pipeline."""
        template = r"""
\section{Skills}
%%SKILLS%%
"""
        user_skills = ["Python", "FastAPI"]
        # Simulate an LLM that hallucinated "Kubernetes"
        content = {
            "SKILLS": r"Skills: Python, FastAPI, Kubernetes, Terraform",
        }

        filled = fill_template(template, content)
        is_valid, violations = validate_resume(filled, user_skills, strict=True)
        assert is_valid is False
        assert "kubernetes" in violations or "terraform" in violations

    @patch("app.services.resume_generator.call_llm")
    def test_generate_with_mock_llm(self, mock_llm):
        """Test resume generation with a mocked LLM response."""
        mock_llm.return_value = json.dumps({
            "SUMMARY": "Experienced Python developer specializing in web development",
            "SKILLS": "Python, FastAPI, React",
            "PROJECTS": r"\item Resume Builder - Built with Python and FastAPI",
            "EXPERIENCE": r"\item Software Engineer at Tech Corp - Used Python and React",
        })

        content = generate_resume_content(
            job_description="Looking for a Python developer",
            matched_skills=["Python", "FastAPI", "React"],
            ranked_projects=[{
                "title": "Resume Builder",
                "description": "Built a resume platform",
                "technologies": "Python, FastAPI",
                "impact": "80% time reduction",
            }],
            experiences=MagicMock(),
            domain="Web Development",
            seniority="Senior",
        )

        assert "SUMMARY" in content
        assert "SKILLS" in content
        assert "PROJECTS" in content
        assert "EXPERIENCE" in content
