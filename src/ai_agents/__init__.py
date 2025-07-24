# Original comprehensive agent

# Multi-agent system components (configured with handoffs)
from .configure_handoffs import AGENTS

# Extract individual agents from configured set
supervisor_agent = AGENTS['supervisor']
github_agent = AGENTS['github']
code_explorer_agent = AGENTS['code_explorer']
analysis_agent = AGENTS['analysis']
save_or_upload_report_agent = AGENTS['save_or_upload_report']

__all__ = [
    'supervisor_agent',
    'github_agent',
    'code_explorer_agent', 
    'analysis_agent',
    'save_or_upload_report_agent'
]