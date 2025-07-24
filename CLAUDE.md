# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Environment Setup:**
- Requires `.env` file with AI endpoint configuration:
  - `CUSTOM_AI_ENDPOINT` - Base URL for AI API
  - `CUSTOM_AI_ENDPOINT_API_KEY` - API key 
  - `DEFAULT_MODEL` - Model name to use
  - Optional: `OPENAI_API_KEY` for OpenAI integration

**Dependencies:**
```bash
# Install with uv (preferred)
uv sync

# Manual installation
pip install -e .
```

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
- `scan_repository_extensions_shared` - Discovery of file types
- `list_all_code_files_shared` - Comprehensive file inventory
- `read_file_smart_shared` - Intelligent chunked file reading
- `scan_files_by_pattern_shared` - Pattern-based file searching (filename, path, content)
- `find_code_references_shared` - Symbol reference analysis (functions, classes, variables)

**Context Operations (`src/tools/context_operations.py`):**
- `add_analysis_findings_shared` - Store analysis results
- `get_file_context_shared` - Retrieve previous analysis for files
- `mark_file_processed_shared` - Track processing progress

**Git Operations (`src/tools/git_operations.py`):**
- Repository cloning with custom host support
- Branch management and protocol flexibility

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

### Repository Structure

- `src/ai_agents/` - Agent definitions and coordination logic
- `src/tools/` - Shared tool implementations
- `cache/` - Session context and temporary data
- `repos/` - Cloned repositories for analysis
- `test_reports/` - Generated analysis reports

### Configuration Requirements

**Confluence Integration:**
- `CONFLUENCE_URL` - Atlassian instance URL
- `CONFLUENCE_EMAIL` - User email
- `CONFLUENCE_API_TOKEN` - API token for authentication

**Git Operations:**
- `GIT_HOST` - Custom Git host (optional)
- `GIT_PROTOCOL` - HTTPS or SSH (optional)

The system is designed to analyze any codebase and generate comprehensive Confluence wiki documentation through coordinated agent workflows.