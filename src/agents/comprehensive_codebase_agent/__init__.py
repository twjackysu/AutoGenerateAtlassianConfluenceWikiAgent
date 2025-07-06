from .agent import comprehensive_codebase_agent
from .tools.file_scanner import list_all_code_files
from .tools.file_reader import read_file_smart
from .tools.cache_manager import (
    get_cached_analysis,
    cache_analysis_result,
    cache_cleanup,
    clear_file_cache
)
from .tools.batch_processor import (
    create_processing_session,
    get_processing_progress,
    get_next_tasks,
    update_task_status
)
from .tools.context_manager import (
    add_analysis_findings,
    get_file_context,
    mark_file_processed,
    get_session_context_summary
)
from .tools.report_generator import (
    generate_report,
    list_available_report_types
)
from .tools.github_tools import (
  clone_github_repo,
)

__all__ = [
    # Main agent
    'comprehensive_codebase_agent',
    
    # File operations
    'list_all_code_files',
    'read_file_smart',
    
    # Cache management
    'get_cached_analysis',
    'cache_analysis_result',
    'cache_cleanup',
    'clear_file_cache',
    
    # Batch processing
    'create_processing_session',
    'get_processing_progress',
    'get_next_tasks',
    'update_task_status',
    
    # Context management
    'add_analysis_findings',
    'get_file_context',
    'mark_file_processed',
    'get_session_context_summary',
    
    # Report generation
    'generate_report',
    'list_available_report_types',
    
    # GitHub integration
    'clone_github_repo'
]