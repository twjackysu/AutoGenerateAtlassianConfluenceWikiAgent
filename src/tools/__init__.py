"""
Shared tools module for multi-agent codebase analysis system.

This module provides common tools that can be used across different agents
while maintaining compatibility with the existing comprehensive codebase agent.
"""

from .file_operations import *
from .git_operations import *
from .batch_operations import *
from .context_operations import *
from .report_operations import *

__all__ = [
    # File operations
    'list_all_code_files_shared',
    'read_file_smart_shared',
    
    # Git operations  
    'clone_github_repo_shared',
    
    # Batch operations
    'create_processing_session_shared',
    'get_processing_progress_shared', 
    'get_next_tasks_shared',
    'update_task_status_shared',
    
    # Context operations
    'add_analysis_findings_shared',
    'get_file_context_shared',
    'mark_file_processed_shared',
    'get_session_context_summary_shared',
    
    # Report operations
    'generate_report_shared',
    'list_available_report_types_shared'
]