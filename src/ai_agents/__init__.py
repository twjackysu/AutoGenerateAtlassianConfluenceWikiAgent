# Original comprehensive agent

# Multi-agent system components (configured with handoffs)
from .configure_handoffs import AGENTS

# Extract individual agents from configured set
supervisor_agent = AGENTS['supervisor']
github_agent = AGENTS['github']
analysis_agent = AGENTS['analysis']
report_agent = AGENTS['report']

__all__ = [
    'supervisor_agent',
    'github_agent', 
    'analysis_agent',
    'report_agent'
]