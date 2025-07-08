"""
Configure handoffs between agents after all agents are created.
This prevents circular import issues while setting up agent coordination.
"""

from pydantic import BaseModel
from typing import Optional
from agents import RunContextWrapper

class SessionHandoffData(BaseModel):
    """Data structure for passing session information between agents"""
    session_id: str
    repo_path: Optional[str] = None
    analysis_goal: Optional[str] = None
    user_requirements: Optional[str] = None
    output_format: Optional[str] = None  # e.g., "table", "list", "summary", "wiki"

async def session_handoff_callback(ctx: RunContextWrapper[None], input_data: SessionHandoffData):
    """Callback function for session handoffs"""
    print(f"🔄 Handoff with session: {input_data.session_id}")
    if input_data.repo_path:
        print(f"📁 Repository: {input_data.repo_path}")
    if input_data.analysis_goal:
        print(f"🎯 Goal: {input_data.analysis_goal}")
    if input_data.user_requirements:
        print(f"📋 User Requirements: {input_data.user_requirements}")
    if input_data.output_format:
        print(f"📊 Output Format: {input_data.output_format}")
    # The handoff data is automatically passed to the receiving agent

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
        handoff(github_agent, on_handoff=session_handoff_callback, input_type=SessionHandoffData),
        handoff(analysis_agent, on_handoff=session_handoff_callback, input_type=SessionHandoffData), 
        handoff(report_agent, on_handoff=session_handoff_callback, input_type=SessionHandoffData)
    ]
    
    # Configure GithubAgent handoffs  
    github_agent.handoffs = [
        handoff(supervisor_agent, on_handoff=session_handoff_callback, input_type=SessionHandoffData)
    ]
    
    # Configure AnalysisAgent handoffs
    analysis_agent.handoffs = [
        handoff(supervisor_agent, on_handoff=session_handoff_callback, input_type=SessionHandoffData),
        handoff(report_agent, on_handoff=session_handoff_callback, input_type=SessionHandoffData)
    ]
    
    # Configure ReportAgent handoffs
    report_agent.handoffs = [
        handoff(supervisor_agent, on_handoff=session_handoff_callback, input_type=SessionHandoffData)
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