"""
Configure handoffs between agents after all agents are created.
This prevents circular import issues while setting up agent coordination.
"""

from pydantic import BaseModel
from typing import Optional
from agents import RunContextWrapper
from src.logging_system import get_logger

class SessionHandoffData(BaseModel):
    """Data structure for passing session information between agents"""
    session_id: str
    repo_path: Optional[str] = None
    analysis_goal: Optional[str] = None
    user_requirements: Optional[str] = None
    output_format: Optional[str] = None  # e.g., "table", "list", "summary", "wiki"

class ReportHandoffData(BaseModel):
    """Data structure for passing report content and storage requirements"""
    session_id: str
    report_content: str
    storage_preference: Optional[str] = "local"  # "local", "confluence", "google_drive", etc.
    custom_filename: Optional[str] = None
    custom_directory: Optional[str] = None
    user_requirements: Optional[str] = None

async def session_handoff_callback(ctx: RunContextWrapper[None], input_data: SessionHandoffData):
    """Callback function for session handoffs"""
    from datetime import datetime
    logger = get_logger(__name__)
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🔄 [{timestamp}] AGENT HANDOFF - SESSION DATA")
    logger.info(f"🆔 Session: {input_data.session_id}")
    if input_data.repo_path:
        logger.info(f"📁 Repository: {input_data.repo_path}")
    if input_data.analysis_goal:
        logger.info(f"🎯 Goal: {input_data.analysis_goal}")
    if input_data.user_requirements:
        logger.info(f"📋 User Requirements: {input_data.user_requirements[:100]}{'...' if len(input_data.user_requirements) > 100 else ''}")
    if input_data.output_format:
        logger.info(f"📊 Output Format: {input_data.output_format}")
    logger.info(f"{'='*60}")
    # The handoff data is automatically passed to the receiving agent

async def report_handoff_callback(ctx: RunContextWrapper[None], input_data: ReportHandoffData):
    """Callback function for report handoffs"""
    from datetime import datetime
    logger = get_logger(__name__)
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"📄 [{timestamp}] REPORT HANDOFF - REPORT DATA")
    logger.info(f"🆔 Session: {input_data.session_id}")
    logger.info(f"💾 Storage preference: {input_data.storage_preference}")
    if input_data.custom_filename:
        logger.info(f"📝 Custom filename: {input_data.custom_filename}")
    if input_data.custom_directory:
        logger.info(f"📂 Custom directory: {input_data.custom_directory}")
    if input_data.user_requirements:
        logger.info(f"📋 User Requirements: {input_data.user_requirements[:100]}{'...' if len(input_data.user_requirements) > 100 else ''}")
    logger.info(f"📊 Report size: {len(input_data.report_content):,} characters")
    logger.info(f"{'='*60}")
    # The handoff data is automatically passed to the receiving agent

def configure_multi_agent_handoffs():
    """Configure handoffs between all agents in the multi-agent system"""
    
    # Import all agents and handoff function
    from .supervisor_agent import supervisor_agent
    from .github_agent import github_agent
    from .code_explorer_agent import code_explorer_agent
    from .analysis_agent import analysis_agent
    from .save_or_upload_report_agent import save_or_upload_report_agent
    from agents import handoff
    
    # Configure SupervisorAgent handoffs with session data passing
    supervisor_agent.handoffs = [
        handoff(github_agent, on_handoff=session_handoff_callback, input_type=SessionHandoffData),
        handoff(code_explorer_agent, on_handoff=session_handoff_callback, input_type=SessionHandoffData),
        handoff(analysis_agent, on_handoff=session_handoff_callback, input_type=SessionHandoffData), 
        handoff(save_or_upload_report_agent, on_handoff=report_handoff_callback, input_type=ReportHandoffData)
    ]
    
    # Configure GithubAgent handoffs  
    github_agent.handoffs = [
        handoff(supervisor_agent, on_handoff=session_handoff_callback, input_type=SessionHandoffData)
    ]
    
    # Configure CodeExplorerAgent handoffs
    code_explorer_agent.handoffs = [
        handoff(supervisor_agent, on_handoff=session_handoff_callback, input_type=SessionHandoffData),
        handoff(analysis_agent, on_handoff=session_handoff_callback, input_type=SessionHandoffData)
    ]
    
    # Configure AnalysisAgent handoffs
    analysis_agent.handoffs = [
        handoff(supervisor_agent, on_handoff=report_handoff_callback, input_type=ReportHandoffData),
        handoff(code_explorer_agent, on_handoff=session_handoff_callback, input_type=SessionHandoffData)
    ]
    
    # Configure SaveOrUploadReportAgent handoffs
    save_or_upload_report_agent.handoffs = [
        handoff(supervisor_agent, on_handoff=session_handoff_callback, input_type=SessionHandoffData)
    ]
    
    logger = get_logger(__name__)
    logger.info("✅ Multi-agent handoffs configured successfully")
    return {
        'supervisor': supervisor_agent,
        'github': github_agent,
        'code_explorer': code_explorer_agent, 
        'analysis': analysis_agent,
        'save_or_upload_report': save_or_upload_report_agent
    }


# Auto-configure handoffs when this module is imported
AGENTS = configure_multi_agent_handoffs()