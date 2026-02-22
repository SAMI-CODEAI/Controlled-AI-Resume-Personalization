"""
Unit tests for the Skill Matcher service.
Tests the core hallucination prevention mechanism.
"""
import pytest
from app.services.skill_matcher import match_skills, _fuzzy_match, _normalize
from app.schemas.schemas import JDAnalysis


class TestNormalize:
    def test_lowercase(self):
        assert _normalize("Python") == "python"

    def test_strip_whitespace(self):
        assert _normalize("  React  ") == "react"

    def test_replace_hyphens(self):
        assert _normalize("Node-JS") == "node js"

    def test_replace_dots(self):
        assert _normalize("Vue.js") == "vuejs"


class TestFuzzyMatch:
    def test_exact_match(self):
        assert _fuzzy_match("Python", ["Python"]) is True

    def test_case_insensitive(self):
        assert _fuzzy_match("python", ["Python"]) is True

    def test_substring_match(self):
        assert _fuzzy_match("react", ["React.js"]) is True

    def test_no_match(self):
        assert _fuzzy_match("Rust", ["Python", "JavaScript"]) is False

    def test_abbreviation_js(self):
        assert _fuzzy_match("js", ["JavaScript"]) is True

    def test_abbreviation_ts(self):
        assert _fuzzy_match("ts", ["TypeScript"]) is True

    def test_postgres_match(self):
        assert _fuzzy_match("postgres", ["PostgreSQL"]) is True

    def test_k8s_match(self):
        assert _fuzzy_match("k8s", ["Kubernetes"]) is True


class TestMatchSkills:
    def test_full_match(self):
        jd = JDAnalysis(
            required_skills=["python", "fastapi"],
            preferred_skills=["docker"],
            keywords=["web"],
            domain="Web",
            seniority="Senior",
        )
        user_skills = ["Python", "FastAPI", "Docker"]
        result = match_skills(jd, user_skills)
        assert result.match_score == 100.0
        assert len(result.matched_skills) == 3
        assert len(result.missing_skills) == 0

    def test_partial_match(self):
        jd = JDAnalysis(
            required_skills=["python", "rust", "go"],
            preferred_skills=["docker"],
            keywords=["backend"],
            domain="Backend",
            seniority="Senior",
        )
        user_skills = ["Python", "Docker"]
        result = match_skills(jd, user_skills)
        assert len(result.matched_skills) == 2
        assert "rust" in result.missing_skills
        assert "go" in result.missing_skills
        assert result.match_score == 50.0

    def test_no_match(self):
        jd = JDAnalysis(
            required_skills=["rust", "go", "c++"],
            preferred_skills=[],
            keywords=[],
            domain="Systems",
            seniority="Senior",
        )
        user_skills = ["Python", "JavaScript"]
        result = match_skills(jd, user_skills)
        assert result.match_score == 0.0
        assert len(result.matched_skills) == 0
        assert len(result.missing_skills) == 3

    def test_missing_skills_not_in_matched(self):
        """Critical: Missing skills must NEVER appear in matched_skills."""
        jd = JDAnalysis(
            required_skills=["python", "kubernetes", "terraform"],
            preferred_skills=["aws"],
            keywords=[],
            domain="DevOps",
            seniority="Senior",
        )
        user_skills = ["Python", "AWS"]
        result = match_skills(jd, user_skills)

        # Verify no overlap between matched and missing
        matched_set = set(result.matched_skills)
        missing_set = set(result.missing_skills)
        assert matched_set & missing_set == set()

    def test_required_match_percentage(self):
        jd = JDAnalysis(
            required_skills=["python", "java", "go", "rust"],
            preferred_skills=[],
            keywords=[],
            domain="Backend",
            seniority="Senior",
        )
        user_skills = ["Python", "Java"]
        result = match_skills(jd, user_skills)
        assert result.required_match_pct == 50.0

    def test_improvement_suggestions_low_match(self):
        jd = JDAnalysis(
            required_skills=["rust", "go", "c++", "assembly"],
            preferred_skills=[],
            keywords=[],
            domain="Systems",
            seniority="Senior",
        )
        user_skills = ["Python"]
        result = match_skills(jd, user_skills)
        assert any("below 50%" in s for s in result.improvement_suggestions)

    def test_empty_user_skills(self):
        jd = JDAnalysis(
            required_skills=["python"],
            preferred_skills=[],
            keywords=[],
            domain="Web",
            seniority="Junior",
        )
        result = match_skills(jd, [])
        assert result.match_score == 0.0
        assert len(result.missing_skills) == 1

    def test_empty_jd_skills(self):
        jd = JDAnalysis(
            required_skills=[],
            preferred_skills=[],
            keywords=[],
            domain="General",
            seniority="Junior",
        )
        result = match_skills(jd, ["Python", "Java"])
        assert result.match_score == 0.0
        assert len(result.matched_skills) == 0
