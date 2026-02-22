"""
Unit tests for the Guardrail Validator service.
Tests the final defense against AI hallucination.
"""
import pytest
from app.services.guardrail_validator import validate_resume, _extract_technologies_from_latex, _normalize


class TestExtractTechnologies:
    def test_extracts_from_skill_section(self):
        latex = r"""
        \section{Skills}
        Skills: Python, JavaScript, React, FastAPI
        """
        techs = _extract_technologies_from_latex(latex)
        assert "python" in techs
        assert "javascript" in techs

    def test_extracts_bold_terms(self):
        latex = r"\textbf{Python} and \textbf{Docker}"
        techs = _extract_technologies_from_latex(latex)
        assert "python" in techs
        assert "docker" in techs

    def test_extracts_from_items(self):
        latex = r"""
        \begin{itemize}
        \item Python, JavaScript
        \item React, Docker
        \end{itemize}
        """
        techs = _extract_technologies_from_latex(latex)
        assert "python" in techs or any("python" in t for t in techs)

    def test_handles_empty_content(self):
        techs = _extract_technologies_from_latex("")
        assert len(techs) == 0


class TestValidateResume:
    def test_valid_resume(self):
        latex = r"""
        \section{Skills}
        Technologies: Python, JavaScript, React
        \section{Experience}
        Developed web applications using \textbf{Python} and \textbf{React}
        """
        user_skills = ["Python", "JavaScript", "React", "Docker"]
        is_valid, violations = validate_resume(latex, user_skills)
        assert is_valid is True
        assert len(violations) == 0

    def test_catches_hallucinated_skill(self):
        latex = r"""
        \section{Skills}
        Technologies: Python, JavaScript, Rust, Kubernetes
        """
        user_skills = ["Python", "JavaScript"]
        is_valid, violations = validate_resume(latex, user_skills, strict=True)
        # Should catch Rust and Kubernetes as unauthorized
        assert "rust" in violations or "kubernetes" in violations

    def test_strict_mode_rejects_any_violation(self):
        latex = r"""
        \section{Skills}
        Skills: Python, Rust
        """
        user_skills = ["Python"]
        is_valid, violations = validate_resume(latex, user_skills, strict=True)
        assert is_valid is False

    def test_non_strict_mode_allows_few_violations(self):
        latex = r"""
        \section{Skills}
        Skills: Python, Rust
        """
        user_skills = ["Python"]
        is_valid, violations = validate_resume(latex, user_skills, strict=False)
        # Non-strict allows up to 3 violations
        assert is_valid is True

    def test_ignores_common_words(self):
        latex = r"""
        Experienced software engineer with strong development skills.
        Used various tools and built multiple applications.
        """
        user_skills = ["Python"]
        is_valid, violations = validate_resume(latex, user_skills)
        # Should not flag common English words
        assert "experienced" not in violations
        assert "software" not in violations

    def test_empty_user_skills(self):
        latex = r"""
        \section{Skills}
        Skills: Python, React
        """
        is_valid, violations = validate_resume(latex, [])
        # With no authorized skills, everything is a violation
        assert is_valid is False

    def test_empty_latex(self):
        is_valid, violations = validate_resume("", ["Python"])
        assert is_valid is True
        assert len(violations) == 0

    def test_substring_skill_matching(self):
        """Test that 'React' matches 'React.js' in user skills."""
        latex = r"""
        \section{Skills}
        Technologies: React
        """
        user_skills = ["React.js"]
        is_valid, violations = validate_resume(latex, user_skills)
        assert is_valid is True
