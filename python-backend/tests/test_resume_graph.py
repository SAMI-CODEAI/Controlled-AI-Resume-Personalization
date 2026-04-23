"""
Tests for LangGraph Resume Generation Routing Logic.

Mocks the low-level LLM and parsing tools to ensure the StateGraph
conditional edges route correctly across permutations:
  - Happy path (no errors)
  - LaTeX validation repair cycle
  - Guardrail validation repair cycle
  - Reflection quality repair cycle
  - Max attempts exhaustion
"""
import pytest
from unittest.mock import patch, MagicMock

from app.agents.graph_state import ResumeGraphState
from app.agents.resume_graph import get_resume_graph


@pytest.fixture
def base_state() -> ResumeGraphState:
    return {
        "job_description": "We need a Python engineer.",
        "template_latex": "\\begin{document} %%SUMMARY%% \\end{document}",
        "authorized_terms": ["python", "django", "project a", "company b"],
        "user_skills": ["python", "django"],
        "user_projects": [],
        "user_experiences": [],
        "attempt_count": 0,
    }


def _mock_tools(mocker):
    mocker.patch("app.agents.nodes.analyze_jd_tool", return_value={"domain": "test", "seniority": "mid"})
    mocker.patch("app.agents.nodes.match_skills_tool", return_value={"matched_skills": ["python"]})
    mocker.patch("app.agents.nodes.rank_projects_tool", return_value=[])
    mocker.patch("app.agents.nodes.generate_content_tool", return_value={"summary": "test content"})
    mocker.patch("app.agents.nodes.fill_template_tool", return_value="filled latex doc")
    mocker.patch("app.agents.nodes.compile_latex_tool", return_value="/output/resume.pdf")


def test_resume_graph_happy_path(base_state):
    """Test that a run with no errors goes straight through with attempt_count=0."""
    with patch("app.agents.nodes.validate_latex_tool", return_value=[]), \
         patch("app.agents.nodes.validate_guardrails_tool", return_value=(True, [])), \
         patch("app.agents.nodes.reflection_tool", return_value=(9, "Great resume!")), \
         patch("app.agents.nodes.analyze_jd_tool", return_value={"domain": "test", "seniority": "mid"}), \
         patch("app.agents.nodes.match_skills_tool", return_value={"matched_skills": ["python"]}), \
         patch("app.agents.nodes.rank_projects_tool", return_value=[]), \
         patch("app.agents.nodes.generate_content_tool", return_value={"summary": "test"}), \
         patch("app.agents.nodes.fill_template_tool", return_value="doc"), \
         patch("app.agents.nodes.compile_latex_tool", return_value="path.pdf"):
        
        graph = get_resume_graph()
        final_state = graph.invoke(base_state)
        
        # Verify it passed through all nodes once
        trace_agents = [e["agent"] for e in final_state["agent_trace"]]
        assert "Content Writer Agent" in trace_agents
        assert "Repair Agent" not in trace_agents
        assert final_state.get("attempt_count") == 0
        assert final_state.get("status") == "success"
        assert final_state.get("pdf_path") == "path.pdf"


def test_resume_graph_guardrail_repair_cycle(base_state):
    """Test that a guardrail violation loops back to repair, then succeeds."""
    mock_guardrail_responses = [
        (False, ["unauthorized hallucinated skill"]),  # Pass 1: fail
        (True, []),  # Pass 2: success
    ]
    
    with patch("app.agents.nodes.validate_latex_tool", return_value=[]), \
         patch("app.agents.nodes.validate_guardrails_tool", side_effect=mock_guardrail_responses), \
         patch("app.agents.nodes.reflection_tool", return_value=(8, "Good")), \
         patch("app.agents.nodes.analyze_jd_tool", return_value={"domain": "test", "seniority": "mid"}), \
         patch("app.agents.nodes.match_skills_tool", return_value={"matched_skills": ["python"]}), \
         patch("app.agents.nodes.rank_projects_tool", return_value=[]), \
         patch("app.agents.nodes.generate_content_tool", return_value={"summary": "test"}), \
         patch("app.agents.nodes.fill_template_tool", return_value="doc"), \
         patch("app.agents.nodes.compile_latex_tool", return_value="path.pdf"):

        graph = get_resume_graph()
        final_state = graph.invoke(base_state)
        
        trace_agents = [e["agent"] for e in final_state["agent_trace"]]
        # Content writer should run twice
        assert trace_agents.count("Content Writer Agent") == 2
        # Repair should run once
        assert trace_agents.count("Repair Agent") == 1
        
        assert final_state.get("attempt_count") == 1
        assert final_state.get("status") == "success"


def test_resume_graph_max_attempts_exhaustion(base_state):
    """Test that repeated guardrail violations hit the loop limit and gracefully abort."""
    # Always fail
    mock_guardrail_responses = [(False, ["bad"])] * 10
    
    with patch("app.agents.nodes.validate_latex_tool", return_value=[]), \
         patch("app.agents.nodes.validate_guardrails_tool", side_effect=mock_guardrail_responses), \
         patch("app.agents.nodes.reflection_tool", return_value=(8, "Good")), \
         patch("app.agents.nodes.analyze_jd_tool", return_value={}), \
         patch("app.agents.nodes.match_skills_tool", return_value={}), \
         patch("app.agents.nodes.rank_projects_tool", return_value=[]), \
         patch("app.agents.nodes.generate_content_tool", return_value={}), \
         patch("app.agents.nodes.fill_template_tool", return_value="doc"), \
         patch("app.agents.nodes.compile_latex_tool", return_value="path.pdf"):

        graph = get_resume_graph()
        final_state = graph.invoke(base_state)
        
        # It should try up to the limit (attempt_count=3)
        assert final_state.get("attempt_count") == 3
        # In our resume_graph logic, when attempt_count >= 3 at the critics, it returns END
        # meaning it gracefully handles it, but since it didn't pass, it skips compiler
        trace_agents = [e["agent"] for e in final_state["agent_trace"]]
        assert "Compiler Agent" not in trace_agents
        
        # Status might not explicitly be "failed" since we gracefully short circuit to END and keep resume.
        # But our router checks for valid pdf_path or such, which wasn't generated.
        assert final_state.get("pdf_path") is None


def test_resume_graph_reflection_repair_cycle(base_state):
    """Test that poor quality triggers a repair loop."""
    mock_reflection_responses = [
        (4, "Poorly written"),  # Pass 1: fail
        (8, "Much better"),     # Pass 2: success
    ]
    
    with patch("app.agents.nodes.validate_latex_tool", return_value=[]), \
         patch("app.agents.nodes.validate_guardrails_tool", return_value=(True, [])), \
         patch("app.agents.nodes.reflection_tool", side_effect=mock_reflection_responses), \
         patch("app.agents.nodes.analyze_jd_tool", return_value={}), \
         patch("app.agents.nodes.match_skills_tool", return_value={}), \
         patch("app.agents.nodes.rank_projects_tool", return_value=[]), \
         patch("app.agents.nodes.generate_content_tool", return_value={}), \
         patch("app.agents.nodes.fill_template_tool", return_value="doc"), \
         patch("app.agents.nodes.compile_latex_tool", return_value="path.pdf"):

        graph = get_resume_graph()
        final_state = graph.invoke(base_state)
        
        # Content writer runs twice
        trace_agents = [e["agent"] for e in final_state["agent_trace"]]
        assert trace_agents.count("Content Writer Agent") == 2
        assert trace_agents.count("Reflection Agent") == 2
        
        assert final_state.get("reflection_score") == 8

