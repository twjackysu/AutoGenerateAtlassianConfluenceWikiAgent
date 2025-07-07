"""
SupervisorAgent - Coordinates multi-agent codebase analysis workflow.

This agent serves as the main coordinator for the multi-agent system,
orchestrating the workflow between GithubAgent, AnalysisAgent, and ReportAgent.
"""

from .agent import supervisor_agent

__all__ = ['supervisor_agent']