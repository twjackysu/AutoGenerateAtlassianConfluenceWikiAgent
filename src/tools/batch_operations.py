"""
Batch operations tools - shared version for multi-agent system.
Simplified version based on the original batch_processor.py.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from agents import function_tool


@function_tool
async def create_processing_session_shared(
    repo_path: str,
    analysis_goal: str,
    strategy: str = "mixed"
) -> str:
    """
    Create a new batch processing session for multi-agent codebase analysis.
    Simplified version for multi-agent coordination.
    
    Args:
        repo_path: Path to the repository to analyze
        analysis_goal: Description of what analysis to perform
        strategy: Batching strategy - "mixed", "by_size", "by_language", or "by_directory"
    
    Returns:
        Session details and initial setup information
    """
    print(f"🔧 [TOOL] create_processing_session_shared(repo_path='{repo_path}', analysis_goal='{analysis_goal}', strategy='{strategy}')")
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())[:8]
        
        # Create session metadata
        session_data = {
            "session_id": session_id,
            "repo_path": repo_path,
            "analysis_goal": analysis_goal,
            "strategy": strategy,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "agent_type": "multi_agent"
        }
        
        # Ensure cache directory exists
        cache_dir = "./cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        # Save session file
        session_file = f"./cache/multi_agent_session_{session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        # Format response
        output = f"""# 🚀 Multi-Agent Processing Session Created

## 📋 Session Information
- **Session ID**: `{session_id}`
- **Repository**: `{repo_path}`
- **Analysis Goal**: {analysis_goal}
- **Strategy**: {strategy}
- **Session File**: `{session_file}`
- **Agent Type**: Multi-Agent System

## 🔄 Next Steps
This session is ready for multi-agent processing. Use the session ID with the appropriate agents:
1. **SupervisorAgent**: Will coordinate the overall process
2. **GithubAgent**: Will handle repository operations if needed
3. **AnalysisAgent**: Will perform code analysis
4. **ReportAgent**: Will generate final reports

Use the session ID `{session_id}` for all subsequent operations.
"""
        
        return output
        
    except Exception as e:
        return f"❌ Error creating multi-agent processing session: {str(e)}"


@function_tool
async def get_processing_progress_shared(session_id: str) -> str:
    """
    Get current progress of a multi-agent processing session.
    
    Args:
        session_id: ID of the processing session
    
    Returns:
        Detailed progress report
    """
    print(f"🔧 [TOOL] get_processing_progress_shared(session_id='{session_id}')")
    try:
        # Find session file
        session_file = f"./cache/multi_agent_session_{session_id}.json"
        if not os.path.exists(session_file):
            return f"❌ Multi-agent session not found: {session_id}"
        
        # Load session data
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        # Format output
        output = f"""# 📊 Multi-Agent Processing Progress Report

## 🎯 Session: {session_id}
- **Repository**: `{session_data.get('repo_path', 'Unknown')}`
- **Analysis Goal**: {session_data.get('analysis_goal', 'Unknown')}
- **Status**: {session_data.get('status', 'Unknown')}
- **Created**: {session_data.get('created_at', 'Unknown')}
- **Agent Type**: {session_data.get('agent_type', 'Unknown')}

## 🤖 Multi-Agent System Status
This session is configured for multi-agent processing. Progress tracking is handled by individual agents.

Use the specific agent tools to track detailed progress:
- **SupervisorAgent**: Overall coordination status
- **AnalysisAgent**: File processing progress  
- **ReportAgent**: Report generation status
"""
        
        return output
        
    except Exception as e:
        return f"❌ Error getting multi-agent progress: {str(e)}"


@function_tool
async def get_next_tasks_shared(session_id: str, limit: int = 5) -> str:
    """
    Get next ready tasks for a multi-agent processing session.
    
    Args:
        session_id: ID of the processing session
        limit: Maximum number of tasks to return
    
    Returns:
        List of ready tasks with details
    """
    print(f"🔧 [TOOL] get_next_tasks_shared(session_id='{session_id}', limit={limit})")
    try:
        # Find session file
        session_file = f"./cache/multi_agent_session_{session_id}.json"
        if not os.path.exists(session_file):
            return f"❌ Multi-agent session not found: {session_id}"
        
        # Load session data
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        output = f"""# 🔄 Multi-Agent Next Tasks (Session: {session_id})

## ✅ Multi-Agent Task Coordination
This is a multi-agent session. Task management is distributed across specialized agents:

### 🤖 Available Agents:
1. **SupervisorAgent**: Coordinates overall workflow
2. **GithubAgent**: Handles repository operations  
3. **AnalysisAgent**: Performs code analysis
4. **ReportAgent**: Generates reports

### 📋 Recommended Workflow:
1. Use **SupervisorAgent** to start the analysis process
2. **SupervisorAgent** will automatically coordinate with other agents
3. Monitor progress through individual agent feedback

## 🚀 Getting Started:
Start with the SupervisorAgent and provide the session ID `{session_id}` and your analysis requirements.
"""
        
        return output
        
    except Exception as e:
        return f"❌ Error getting multi-agent next tasks: {str(e)}"


@function_tool
async def update_task_status_shared(
    session_id: str,
    task_id: str,
    status: str,
    error_message: Optional[str] = None
) -> str:
    """
    Update the status of a specific task in a multi-agent processing session.
    
    Args:
        session_id: ID of the processing session
        task_id: ID of the task to update
        status: New status - "pending", "in_progress", "completed", "failed", "skipped"
        error_message: Error message if status is "failed"
    
    Returns:
        Update confirmation
    """
    print(f"🔧 [TOOL] update_task_status_shared(session_id='{session_id}', task_id='{task_id}', status='{status}')")
    try:
        # Find session file
        session_file = f"./cache/multi_agent_session_{session_id}.json"
        if not os.path.exists(session_file):
            return f"❌ Multi-agent session not found: {session_id}"
        
        # Load session data
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        # Update session status if needed
        if status == "completed" and task_id == "overall":
            session_data["status"] = "completed"
        elif status == "failed" and task_id == "overall":
            session_data["status"] = "failed"
        elif status == "in_progress" and task_id == "overall":
            session_data["status"] = "in_progress"
        
        # Add task update record
        if "task_updates" not in session_data:
            session_data["task_updates"] = []
        
        session_data["task_updates"].append({
            "task_id": task_id,
            "status": status,
            "error_message": error_message,
            "updated_at": datetime.now().isoformat()
        })
        
        # Save updated session
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        output = f"""# ✅ Multi-Agent Task Status Updated

## 📝 Update Details
- **Session**: {session_id}
- **Task**: {task_id}  
- **New Status**: {status}
- **Error Message**: {error_message or "None"}
- **Updated At**: {datetime.now().isoformat()}

## 📊 Session Status
- **Overall Status**: {session_data.get('status', 'Unknown')}
- **Total Updates**: {len(session_data.get('task_updates', []))}

Task status updated successfully in multi-agent session.
"""
        
        return output
        
    except Exception as e:
        return f"❌ Error updating multi-agent task status: {str(e)}"