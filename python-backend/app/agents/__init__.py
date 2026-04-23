"""
Multi-Agent Orchestration Package.

This package implements the FAANG-grade agentic architecture using LangGraph
StateGraphs. Eight specialized agents collaborate to generate, critique,
self-repair, and reflect on resume quality before final compilation.

Agents:
    - JD Analyst Agent       : Parses job descriptions into structured requirements
    - Skill Matcher Agent    : Aligns user skills with JD requirements (anti-hallucination)
    - Project Ranker Agent   : Scores and ranks projects by job relevance
    - Content Writer Agent   : Generates LaTeX placeholder content
    - LaTeX Critic Agent     : Validates structural correctness of LaTeX output
    - Guardrail Critic Agent : Enforces no unauthorized skill/entity hallucination
    - Repair Agent           : Self-heals based on critic feedback (cyclical loop)
    - Reflection Agent       : Scores overall resume quality and triggers re-generation
    - Compiler Agent         : Compiles LaTeX → PDF
"""
from app.agents.resume_graph import get_resume_graph
from app.agents.chat_graph import get_chat_graph
from app.agents.agent_memory import AgentMemory

__all__ = ["get_resume_graph", "get_chat_graph", "AgentMemory"]
