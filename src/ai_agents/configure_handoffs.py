"""
Configure handoffs between agents after all agents are created.
This prevents circular import issues while setting up agent coordination.
"""

def configure_multi_agent_handoffs():
    """Configure handoffs between all agents in the multi-agent system"""
    
    # Import all agents
    from .supervisor_agent import supervisor_agent
    from .github_agent import github_agent
    from .analysis_agent import analysis_agent
    from .report_agent import report_agent
    
    # Configure SupervisorAgent handoffs
    supervisor_agent.handoffs = [github_agent, analysis_agent, report_agent]
    
    # Configure GithubAgent handoffs  
    github_agent.handoffs = [supervisor_agent]
    
    # Configure AnalysisAgent handoffs
    analysis_agent.handoffs = [supervisor_agent, report_agent]
    
    # Configure ReportAgent handoffs
    report_agent.handoffs = [supervisor_agent]
    
    print("✅ Multi-agent handoffs configured successfully")
    return {
        'supervisor': supervisor_agent,
        'github': github_agent, 
        'analysis': analysis_agent,
        'report': report_agent
    }


# Auto-configure handoffs when this module is imported
AGENTS = configure_multi_agent_handoffs()