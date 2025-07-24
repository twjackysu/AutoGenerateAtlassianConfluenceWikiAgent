# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

### Multi-Agent System Design

The system implements a coordinated multi-agent architecture for automated codebase analysis and Confluence wiki generation:

**Agent Hierarchy:**
- **SupervisorAgent**: Main orchestrator that receives user requests and coordinates all other agents
- **GithubAgent**: Handles Git repository operations (cloning, updating, branch management)
- **CodeExplorerAgent**: Specialized in file discovery, smart reading, pattern searching, and code reference analysis
- **AnalysisAgent**: Focuses on semantic analysis, pattern recognition, and architectural analysis
- **ReportAgent**: Generates professional reports from analysis findings
- **SaveOrUploadReportAgent**: Handles report storage (local files, Confluence wiki pages)

### Agent Coordination Mechanism

**Session-Based Context Sharing:**
- Each analysis session gets a unique `session_id`
- Shared context stored in `./cache/multi_agent_context_{session_id}.json`
- Context includes findings, processed files, and agent contributions

**Handoff System:**
- Defined in `src/ai_agents/configure_handoffs.py`
- Uses `SessionHandoffData` and `ReportHandoffData` for structured data passing
- Bidirectional handoffs between related agents (e.g., CodeExplorer ↔ Analysis)

### Tool Architecture

**File Operations (`src/tools/file_operations.py`):**
- `scan_repository_extensions_shared` - Discovery of file types with categorization (code/config/other)
- `list_all_code_files_shared` - Comprehensive file inventory with metadata, size analysis, and processing recommendations
- `read_file_smart_shared` - Intelligent chunked file reading with automatic/manual chunking strategies
- `save_report_file_shared` - Save reports to directories with automatic creation and file statistics
- `search_confluence_spaces_shared` - Search Confluence spaces using API credentials
- `search_confluence_pages_shared` - Search pages in Confluence spaces with title filtering
- `get_confluence_page_info_shared` - Get detailed Confluence page information and metadata
- `upload_to_confluence_shared` - Upload/update reports to Confluence with markdown conversion
- `search_files_by_pattern_shared` - Pattern-based file searching (filename, path, content) with smart filtering
- `find_code_references_shared` - Symbol reference analysis using AST parsing and regex patterns

**Context Operations (`src/tools/context_operations.py`):**
- `add_analysis_findings_shared` - Store analysis results in JSON context files
- `get_file_context_shared` - Retrieve previous analysis for specific files
- `get_session_summary_shared` - Get comprehensive session summary with statistics
- `get_session_context_summary_shared` - Get session context summary for reporting
- `merge_analysis_contexts_shared` - Merge analysis contexts with conflict resolution
- `cache_exploration_results_shared` - Cache exploration data for multi-agent sharing
- `get_shared_exploration_results_shared` - Retrieve cached exploration data
- `cache_file_content_shared` - Cache file content for agent access
- `get_cached_file_content_shared` - Retrieve cached file content

**Batch Operations (`src/tools/batch_operations.py`):**
- `create_processing_session_shared` - Create batch processing sessions with unique IDs
- `get_processing_progress_shared` - Get processing progress from cached session files
- `get_next_tasks_shared` - Get next ready tasks for multi-agent coordination
- `update_task_status_shared` - Update task status with error handling

**Git Operations (`src/tools/git_operations.py`):**
- `clone_github_repo_shared` - Repository cloning with custom hosts, SSH support, branch selection, and automatic cleanup

**Report Operations (`src/tools/report_operations.py`):**
- `generate_report_shared` - Generate comprehensive reports from cached analysis findings
- `list_available_report_types_shared` - List available report types with descriptions

**Formatting Tools (`src/tools/formatting_tools.py`):**
- `convert_json_to_markdown_table` - Convert JSON data to formatted markdown tables with column selection
- `format_findings_as_list` - Format JSON findings as structured lists with grouping and field selection
- `extract_unique_fields` - Extract all unique field names from JSON data for analysis
- `generate_summary_stats` - Generate summary statistics from JSON findings data

### Key Design Patterns

**Separation of Concerns:**
- CodeExplorerAgent: File system navigation and code discovery
- AnalysisAgent: Semantic understanding and pattern extraction
- Clean separation prevents tool overlap and maintains focused responsibilities

**Shared Tool Library:**
- All tools suffixed with `_shared` for multi-agent coordination
- Tools designed to work with `session_id` for context continuity
- Consistent error handling and output formatting

**Agent Workflow:**
1. SupervisorAgent receives user request and creates session
2. GithubAgent handles repository preparation (if needed)
3. CodeExplorerAgent performs file discovery and content extraction
4. AnalysisAgent conducts semantic analysis and pattern recognition
5. ReportAgent formats findings into professional documentation
6. SaveOrUploadReportAgent handles final delivery (files/Confluence)

### Agent Responsibilities & Tools

#### SupervisorAgent (Main Orchestrator)
**Responsibilities:**
- **Workflow Orchestration**: Receive and interpret user analysis requests  
- **Session Management**: Create processing sessions with unique session_id
- **Agent Coordination**: Coordinate workflow between all other agents using structured handoff data
- **Progress Monitoring**: Track overall progress and update task status across agents
- **Quality Assurance**: Ensure comprehensive analysis completion and handle failures
- **User Experience**: Provide clear communication and status updates throughout the workflow
- **Strategic Planning**: Determine optimal analysis approach (GitHub repo vs local, analysis type, etc.)

**Key Workflow Patterns:**
1. **GitHub Repository Analysis**: Session → GithubAgent → AnalysisAgent → ReportAgent
2. **Local Repository Analysis**: Session → AnalysisAgent → ReportAgent  
3. **Specific Analysis Goals**: Parse user requirements for targeted analysis (API inventory, security, etc.)

**Tools:**
- `create_processing_session_shared` - Initialize analysis sessions with session_id
- `get_processing_progress_shared` - Monitor analysis progress across agents
- `update_task_status_shared` - Track task completion status and handle failures
- `get_session_context_summary_shared` - Get comprehensive session overview for decision-making

**Handoffs TO:**
- GithubAgent (for repository operations)
- CodeExplorerAgent (for file discovery) 
- AnalysisAgent (for code analysis)
- ReportAgent (for report generation)
- SaveOrUploadReportAgent (for report delivery)

**Handoffs FROM:** 
- GithubAgent (completion status)
- CodeExplorerAgent (exploration results)
- AnalysisAgent (analysis completion)
- ReportAgent (report generation completion)
- SaveOrUploadReportAgent (delivery confirmation)

#### GithubAgent (Repository Operations)
**Responsibilities:**
- Clone GitHub repositories to `repos/` folder
- Handle repository updates and branch management
- Support custom Git hosts and SSH/HTTPS protocols

**Tools:**
- `clone_github_repo_shared` - Git repository operations

**Handoffs FROM:** SupervisorAgent
**Handoffs TO:** SupervisorAgent

#### CodeExplorerAgent (File Discovery & Caching)
**Responsibilities:**
- **EXCLUSIVE file access** - Only agent that reads files directly
- Discover file types and comprehensive file inventory
- Smart chunked reading for large files
- Cache all file content for AnalysisAgent consumption
- Pattern-based searching and code reference analysis

**Tools:**
- `scan_repository_extensions_shared` - File type discovery
- `list_all_code_files_shared` - Comprehensive file listing
- `read_file_smart_shared` - Intelligent file reading
- `search_files_by_pattern_shared` - Pattern-based searches
- `find_code_references_shared` - Symbol reference tracking
- `cache_exploration_results_shared` - Cache exploration data for other agents
- `get_shared_exploration_results_shared` - Retrieve cached exploration data
- `cache_file_content_shared` - Cache file content for AnalysisAgent access
- `get_cached_file_content_shared` - Retrieve cached file content

**Handoffs FROM:** SupervisorAgent, AnalysisAgent
**Handoffs TO:** SupervisorAgent, AnalysisAgent

#### AnalysisAgent (Semantic Analysis)
**Responsibilities:**
- **NO direct file access** - Uses only cached content from CodeExplorerAgent
- Semantic analysis, pattern recognition, API discovery
- Architecture analysis and dependency mapping
- Store analysis findings with session context
- **Can request additional exploration** from CodeExplorerAgent when needed

**Tools:**
- `add_analysis_findings_shared` - Store analysis results (MANDATORY for each file)
- `get_file_context_shared` - Retrieve previous analysis
- `get_session_summary_shared` - Get session summary with statistics
- `get_shared_exploration_results_shared` - Access cached exploration data from CodeExplorerAgent
- `get_cached_file_content_shared` - Retrieve cached file content from CodeExplorerAgent

**Handoffs FROM:** SupervisorAgent, CodeExplorerAgent
**Handoffs TO:** SupervisorAgent, CodeExplorerAgent, ReportAgent

#### ReportAgent (Documentation Generation)
**Responsibilities:**
- Generate professional markdown reports from analysis findings
- Use natural LLM markdown formatting abilities
- Format data as tables, lists, or custom structures based on user requirements
- Create comprehensive documentation with executive summaries

**Tools:**
- `get_session_context_summary_shared` - Access session data and analysis findings
- `get_file_context_shared` - Retrieve specific file analysis

**Handoffs FROM:** SupervisorAgent, AnalysisAgent
**Handoffs TO:** SupervisorAgent, SaveOrUploadReportAgent

#### SaveOrUploadReportAgent (Report Delivery)
**Responsibilities:**
- Save reports to local files or upload to Confluence wiki
- Handle multiple output formats
- Manage report delivery preferences

**Tools:**
- `save_report_file_shared` - Save reports to local files
- `upload_to_confluence_shared` - Upload reports to Confluence wiki
- `search_confluence_spaces_shared` - Search available Confluence spaces
- `search_confluence_pages_shared` - Search pages in Confluence spaces
- `get_confluence_page_info_shared` - Get detailed Confluence page information

**Handoffs FROM:** ReportAgent
**Handoffs TO:** SupervisorAgent

### Handoff Data Structure

**SessionHandoffData Format:**
```json
{
  "session_id": "unique_session_identifier",
  "repo_path": "repos/repository_name",
  "analysis_goal": "user's analysis requirements", 
  "user_requirements": "specific format and content needs"
}
```

**ReportHandoffData Format:**
```json
{
  "session_id": "unique_session_identifier",
  "report_content": "generated_markdown_content",
  "output_format": "preferred_delivery_format",
  "user_requirements": "original_user_request"
}
```

### Repository Structure

- `src/ai_agents/` - Agent definitions and coordination logic
- `src/tools/` - Shared tool implementations
- `cache/` - Session context and temporary data
- `repos/` - Cloned repositories for analysis

### Configuration Requirements

**AI Endpoint Configuration (Primary):**
- `CUSTOM_AI_ENDPOINT` - AI service URL (e.g., https://api.rdsec.trendmicro.com/prod/aiendpoint/v1)
- `CUSTOM_AI_ENDPOINT_API_KEY` - API authentication key  
- `DEFAULT_MODEL` - AI model to use (e.g., "claude-4-sonnet")

**Confluence Integration:**
- `CONFLUENCE_URL` - Atlassian instance URL (e.g., https://trendmicro.atlassian.net/wiki)
- `CONFLUENCE_USERNAME` - User email address
- `CONFLUENCE_TOKEN` - API token for authentication

**Git Operations:**
- `GIT_HOST` - Custom Git host (optional, default: github.com)
- `GIT_PROTOCOL` - HTTPS or SSH protocol (optional)
- `SSH_KEY_PATH` - SSH private key path (for SSH protocol)

The system is designed to analyze any codebase and generate comprehensive Confluence wiki documentation through coordinated agent workflows.