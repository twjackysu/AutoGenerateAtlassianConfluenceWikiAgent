"""
Configure handoffs between agents after all agents are created.
This prevents circular import issues while setting up agent coordination.
"""

from pydantic import BaseModel
from typing import Optional

class SessionHandoffData(BaseModel):
    """Data structure for passing session information between agents"""
    session_id: str
    repo_path: Optional[str] = None
    analysis_goal: Optional[str] = None
    user_requirements: Optional[str] = None

def configure_multi_agent_handoffs():
    """Configure handoffs between all agents in the multi-agent system"""
    
    # Import all agents and handoff function
    from .supervisor_agent import supervisor_agent
    from .github_agent import github_agent
    from .analysis_agent import analysis_agent
    from .report_agent import report_agent
    from agents import handoff
    
    # Configure SupervisorAgent handoffs with session data passing
    supervisor_agent.handoffs = [
        handoff(github_agent, input_type=SessionHandoffData),
        handoff(analysis_agent, input_type=SessionHandoffData), 
        handoff(report_agent, input_type=SessionHandoffData)
    ]
    
    # Configure GithubAgent handoffs  
    github_agent.handoffs = [
        handoff(supervisor_agent, input_type=SessionHandoffData)
    ]
    
    # Configure AnalysisAgent handoffs
    analysis_agent.handoffs = [
        handoff(supervisor_agent, input_type=SessionHandoffData),
        handoff(report_agent, input_type=SessionHandoffData)
    ]
    
    # Configure ReportAgent handoffs
    report_agent.handoffs = [
        handoff(supervisor_agent, input_type=SessionHandoffData)
    ]
    
    print("✅ Multi-agent handoffs configured successfully")
    return {
        'supervisor': supervisor_agent,
        'github': github_agent, 
        'analysis': analysis_agent,
        'report': report_agent
    }


# Auto-configure handoffs when this module is imported
AGENTS = configure_multi_agent_handoffs()