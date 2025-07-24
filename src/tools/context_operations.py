"""
Context operations tools - shared version for multi-agent system.
Simplified version based on the original context_manager.py.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from agents import function_tool


@function_tool
async def add_analysis_findings_shared(
    session_id: str,
    findings: str,
    source_file: str
) -> str:
    """
    Add analysis findings to the shared context for multi-agent coordination.
    
    Args:
        session_id: ID of the processing session
        findings: JSON string containing analysis results
        source_file: Source file that was analyzed
    
    Returns:
        Confirmation of findings addition
    """
    try:
        # Ensure cache directory exists
        cache_dir = "./cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load or create context file
        context_file = f"./cache/multi_agent_context_{session_id}.json"
        if os.path.exists(context_file):
            with open(context_file, 'r', encoding='utf-8') as f:
                context_data = json.load(f)
        else:
            context_data = {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "findings": [],
                "processed_files": [],
                "agent_contributions": {}
            }
        
        # Add new findings
        try:
            findings_dict = json.loads(findings) if isinstance(findings, str) else findings
        except json.JSONDecodeError:
            findings_dict = {"raw_findings": findings}
        
        finding_entry = {
            "source_file": source_file,
            "findings": findings_dict,
            "added_at": datetime.now().isoformat(),
            "agent_type": "multi_agent"
        }
        
        context_data["findings"].append(finding_entry)
        if source_file not in context_data["processed_files"]:
            context_data["processed_files"].append(source_file)
        
        context_data["last_updated"] = datetime.now().isoformat()
        
        # Save updated context
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(context_data, f, indent=2, ensure_ascii=False)
        
        output = f"""# ✅ Analysis Findings Added (Multi-Agent)

## 📝 Addition Details
- **Session**: {session_id}
- **Source File**: `{source_file}`
- **Findings Added**: {len(findings_dict)} items
- **Added At**: {datetime.now().isoformat()}

## 📊 Context Summary
- **Total Findings**: {len(context_data['findings'])}
- **Processed Files**: {len(context_data['processed_files'])}
- **Context File**: `{context_file}`

Findings successfully added to shared multi-agent context.
"""
        
        return output
        
    except Exception as e:
        return f"❌ Error adding analysis findings: {str(e)}"


@function_tool
async def get_file_context_shared(
    session_id: str,
    file_path: str
) -> str:
    """
    Get context information for a specific file from multi-agent analysis.
    
    Args:
        session_id: ID of the processing session
        file_path: Path to the file to get context for
    
    Returns:
        Context information for the file
    """
    try:
        # Load context file
        context_file = f"./cache/multi_agent_context_{session_id}.json"
        if not os.path.exists(context_file):
            return f"❌ Multi-agent context not found for session: {session_id}"
        
        with open(context_file, 'r', encoding='utf-8') as f:
            context_data = json.load(f)
        
        # Find relevant findings for this file
        relevant_findings = []
        for finding in context_data.get("findings", []):
            if finding["source_file"] == file_path:
                relevant_findings.append(finding)
        
        if not relevant_findings:
            output = f"""# 📄 File Context: {os.path.basename(file_path)} (Multi-Agent)

## 📊 Context Information
- **Session**: {session_id}
- **File**: `{file_path}`
- **Status**: No previous analysis found

## 🔍 Related Context
No specific analysis findings available for this file yet.
"""
        else:
            output = f"""# 📄 File Context: {os.path.basename(file_path)} (Multi-Agent)

## 📊 Context Information
- **Session**: {session_id}
- **File**: `{file_path}`
- **Analysis Entries**: {len(relevant_findings)}

## 🔍 Analysis History
"""
            for i, finding in enumerate(relevant_findings, 1):
                output += f"### Analysis {i} ({finding.get('added_at', 'Unknown time')})\n"
                findings_data = finding.get('findings', {})
                
                # Handle both dictionary and list formats
                if isinstance(findings_data, dict):
                    for key, value in findings_data.items():
                        output += f"- **{key}**: {value}\n"
                elif isinstance(findings_data, list):
                    for j, item in enumerate(findings_data):
                        output += f"- **Item {j+1}**: {item}\n"
                else:
                    output += f"- **Raw data**: {findings_data}\n"
                output += "\n"
        
        return output
        
    except Exception as e:
        return f"❌ Error getting file context: {str(e)}"


@function_tool
async def mark_file_processed_shared(
    session_id: str,
    file_path: str,
    processing_agent: str = "unknown"
) -> str:
    """
    Mark a file as processed by a specific agent in the multi-agent system.
    
    Args:
        session_id: ID of the processing session
        file_path: Path to the file that was processed
        processing_agent: Name of the agent that processed the file
    
    Returns:
        Confirmation of file processing status
    """
    try:
        # Ensure cache directory exists
        cache_dir = "./cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load or create context file
        context_file = f"./cache/multi_agent_context_{session_id}.json"
        if os.path.exists(context_file):
            with open(context_file, 'r', encoding='utf-8') as f:
                context_data = json.load(f)
        else:
            context_data = {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "findings": [],
                "processed_files": [],
                "agent_contributions": {}
            }
        
        # Mark file as processed
        if file_path not in context_data["processed_files"]:
            context_data["processed_files"].append(file_path)
        
        # Track agent contribution
        if processing_agent not in context_data["agent_contributions"]:
            context_data["agent_contributions"][processing_agent] = []
        if file_path not in context_data["agent_contributions"][processing_agent]:
            context_data["agent_contributions"][processing_agent].append(file_path)
        
        context_data["last_updated"] = datetime.now().isoformat()
        
        # Save updated context
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(context_data, f, indent=2, ensure_ascii=False)
        
        output = f"""# ✅ File Marked as Processed (Multi-Agent)

## 📝 Processing Details
- **Session**: {session_id}
- **File**: `{file_path}`
- **Processing Agent**: {processing_agent}
- **Processed At**: {datetime.now().isoformat()}

## 📊 Session Progress
- **Total Processed Files**: {len(context_data['processed_files'])}
- **Agent Contributions**: {len(context_data['agent_contributions'])} agents

File successfully marked as processed in multi-agent context.
"""
        
        return output
        
    except Exception as e:
        return f"❌ Error marking file as processed: {str(e)}"


@function_tool
async def get_session_context_summary_shared(session_id: str) -> str:
    """
    Get a summary of the entire session context for multi-agent coordination.
    
    Args:
        session_id: ID of the processing session
    
    Returns:
        Comprehensive context summary
    """
    try:
        # Load context file
        context_file = f"./cache/multi_agent_context_{session_id}.json"
        if not os.path.exists(context_file):
            return f"❌ Multi-agent context not found for session: {session_id}"
        
        with open(context_file, 'r', encoding='utf-8') as f:
            context_data = json.load(f)
        
        # Generate summary
        output = f"""# 📊 Multi-Agent Session Context Summary

## 🎯 Session Overview
- **Session ID**: {session_id}
- **Created**: {context_data.get('created_at', 'Unknown')}
- **Last Updated**: {context_data.get('last_updated', 'Unknown')}

## 📈 Processing Statistics
- **Total Findings**: {len(context_data.get('findings', []))}
- **Processed Files**: {len(context_data.get('processed_files', []))}
- **Contributing Agents**: {len(context_data.get('agent_contributions', {}))}

## 🤖 Agent Contributions
"""
        
        for agent, files in context_data.get('agent_contributions', {}).items():
            output += f"- **{agent}**: {len(files)} files processed\n"
        
        if context_data.get('processed_files'):
            output += f"""

## 📁 Processed Files
"""
            for i, file_path in enumerate(context_data['processed_files'][:10], 1):
                output += f"{i}. `{file_path}`\n"
            
            if len(context_data['processed_files']) > 10:
                output += f"... and {len(context_data['processed_files']) - 10} more files\n"
        
        # Show recent findings
        recent_findings = context_data.get('findings', [])[-5:]  # Last 5 findings
        if recent_findings:
            output += f"""

## 🔍 Recent Findings
"""
            for finding in recent_findings:
                output += f"- **{finding.get('source_file', 'Unknown')}**: {len(finding.get('findings', {}))} items ({finding.get('added_at', 'Unknown time')})\n"
        
        return output
        
    except Exception as e:
        return f"❌ Error getting session context summary: {str(e)}"


@function_tool
async def cache_exploration_results_shared(
    session_id: str,
    exploration_type: str,
    exploration_data: str,
    metadata: Optional[str] = None
) -> str:
    """
    Cache exploration results from CodeExplorerAgent for shared access.
    
    Args:
        session_id: ID of the processing session
        exploration_type: Type of exploration (file_inventory, pattern_search, reference_analysis)
        exploration_data: JSON string containing exploration results
        metadata: Optional metadata about the exploration
    
    Returns:
        Confirmation of caching operation
    """
    try:
        # Ensure cache directory exists
        cache_dir = "./cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load or create shared context file
        context_file = f"./cache/shared_context_{session_id}.json"
        if os.path.exists(context_file):
            with open(context_file, 'r', encoding='utf-8') as f:
                shared_context = json.load(f)
        else:
            shared_context = {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "exploration_results": {},
                "processing_status": {
                    "processed_files": [],
                    "file_contexts": {}
                },
                "content_cache": {},
                "analysis_findings": []
            }
        
        # Parse exploration data
        try:
            exploration_dict = json.loads(exploration_data) if isinstance(exploration_data, str) else exploration_data
        except json.JSONDecodeError:
            exploration_dict = {"raw_data": exploration_data}
        
        # Cache the exploration results
        if exploration_type not in shared_context["exploration_results"]:
            shared_context["exploration_results"][exploration_type] = {}
        
        shared_context["exploration_results"][exploration_type].update(exploration_dict)
        shared_context["last_updated"] = datetime.now().isoformat()
        
        # Add metadata if provided
        if metadata:
            try:
                metadata_dict = json.loads(metadata) if isinstance(metadata, str) else metadata
                shared_context["exploration_results"][exploration_type]["_metadata"] = metadata_dict
            except json.JSONDecodeError:
                shared_context["exploration_results"][exploration_type]["_metadata"] = {"note": metadata}
        
        # Save updated shared context
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(shared_context, f, indent=2, ensure_ascii=False)
        
        output = f"""✅ **Exploration Results Cached Successfully**

📊 **Cache Details**
- **Session**: {session_id}
- **Exploration Type**: {exploration_type}
- **Data Size**: {len(exploration_data):,} characters
- **Cached At**: {datetime.now().isoformat()}

🗃️ **Shared Context Summary**
- **Total Exploration Types**: {len(shared_context['exploration_results'])}
- **Processed Files**: {len(shared_context['processing_status']['processed_files'])}
- **Cached Content**: {len(shared_context['content_cache'])} files

Exploration results are now available for other agents to access.
"""
        
        return output
        
    except Exception as e:
        return f"❌ Error caching exploration results: {str(e)}"


@function_tool
async def get_shared_exploration_results_shared(
    session_id: str,
    exploration_type: Optional[str] = None
) -> str:
    """
    Retrieve cached exploration results from shared context.
    
    Args:
        session_id: ID of the processing session
        exploration_type: Specific type to retrieve, or None for all results
    
    Returns:
        Exploration results or summary
    """
    try:
        # Load shared context file
        context_file = f"./cache/shared_context_{session_id}.json"
        if not os.path.exists(context_file):
            return f"❌ Shared context not found for session: {session_id}"
        
        with open(context_file, 'r', encoding='utf-8') as f:
            shared_context = json.load(f)
        
        exploration_results = shared_context.get("exploration_results", {})
        
        if exploration_type:
            # Return specific exploration type
            if exploration_type in exploration_results:
                specific_results = exploration_results[exploration_type]
                return f"""# 🔍 {exploration_type.replace('_', ' ').title()} Results

## 📊 Results Summary
- **Session**: {session_id}
- **Type**: {exploration_type}
- **Last Updated**: {shared_context.get('last_updated', 'Unknown')}

## 📋 Results Data
```json
{json.dumps(specific_results, indent=2, ensure_ascii=False)}
```

Use this data for analysis and processing.
"""
            else:
                return f"❌ No results found for exploration type: {exploration_type}"
        
        else:
            # Return summary of all exploration results
            output = f"""# 🗃️ All Exploration Results Summary

## 📊 Session Overview
- **Session ID**: {session_id}
- **Last Updated**: {shared_context.get('last_updated', 'Unknown')}
- **Available Exploration Types**: {len(exploration_results)}

## 🔍 Available Exploration Results
"""
            
            for exp_type, exp_data in exploration_results.items():
                data_size = len(json.dumps(exp_data)) if isinstance(exp_data, dict) else len(str(exp_data))
                metadata = exp_data.get('_metadata', {}) if isinstance(exp_data, dict) else {}
                
                output += f"""
### {exp_type.replace('_', ' ').title()}
- **Data Size**: {data_size:,} characters
- **Keys**: {list(exp_data.keys()) if isinstance(exp_data, dict) else 'Raw data'}
- **Metadata**: {metadata}
"""
            
            output += f"""

## 💡 Usage
To get specific exploration results, use:
`get_shared_exploration_results_shared(session_id="{session_id}", exploration_type="specific_type")`
"""
            
            return output
        
    except Exception as e:
        return f"❌ Error getting shared exploration results: {str(e)}"


@function_tool
async def cache_file_content_shared(
    session_id: str,
    file_path: str,
    content_data: str,
    metadata: Optional[str] = None
) -> str:
    """
    Cache file content in shared context for analysis access.
    
    Args:
        session_id: ID of the processing session
        file_path: Path to the file being cached
        content_data: File content or chunked content data
        metadata: Optional metadata about the file
    
    Returns:
        Confirmation of caching operation
    """
    try:
        # Ensure cache directory exists
        cache_dir = "./cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load shared context file
        context_file = f"./cache/shared_context_{session_id}.json"
        if os.path.exists(context_file):
            with open(context_file, 'r', encoding='utf-8') as f:
                shared_context = json.load(f)
        else:
            return f"❌ Shared context not found for session: {session_id}. Create exploration results first."
        
        # Parse content data
        try:
            content_dict = json.loads(content_data) if isinstance(content_data, str) else content_data
        except json.JSONDecodeError:
            content_dict = {"raw_content": content_data}
        
        # Cache the file content
        shared_context["content_cache"][file_path] = {
            "content_data": content_dict,
            "cached_at": datetime.now().isoformat(),
            "metadata": json.loads(metadata) if metadata else {}
        }
        
        shared_context["last_updated"] = datetime.now().isoformat()
        
        # Save updated shared context
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(shared_context, f, indent=2, ensure_ascii=False)
        
        output = f"""✅ **File Content Cached Successfully**

📁 **File Details**
- **Session**: {session_id}
- **File Path**: `{file_path}`
- **Content Size**: {len(content_data):,} characters
- **Cached At**: {datetime.now().isoformat()}

🗃️ **Cache Status**
- **Total Cached Files**: {len(shared_context['content_cache'])}
- **Available for Analysis**: Ready

File content is now available for AnalysisAgent to access.
"""
        
        return output
        
    except Exception as e:
        return f"❌ Error caching file content: {str(e)}"


@function_tool
async def get_cached_file_content_shared(
    session_id: str,
    file_path: str
) -> str:
    """
    Retrieve cached file content from shared context.
    
    Args:
        session_id: ID of the processing session
        file_path: Path to the file to retrieve
    
    Returns:
        Cached file content and metadata
    """
    try:
        # Load shared context file
        context_file = f"./cache/shared_context_{session_id}.json"
        if not os.path.exists(context_file):
            return f"❌ Shared context not found for session: {session_id}"
        
        with open(context_file, 'r', encoding='utf-8') as f:
            shared_context = json.load(f)
        
        content_cache = shared_context.get("content_cache", {})
        
        if file_path not in content_cache:
            return f"❌ File content not cached: {file_path}"
        
        cached_file = content_cache[file_path]
        content_data = cached_file["content_data"]
        cached_at = cached_file.get("cached_at", "Unknown")
        metadata = cached_file.get("metadata", {})
        
        output = f"""# 📁 Cached File Content: {os.path.basename(file_path)}

## 📊 File Information
- **Session**: {session_id}
- **File Path**: `{file_path}`
- **Cached At**: {cached_at}
- **Metadata**: {metadata}

## 📝 Content Data
```json
{json.dumps(content_data, indent=2, ensure_ascii=False)}
```

This cached content is ready for analysis.
"""
        
        return output
        
    except Exception as e:
        return f"❌ Error getting cached file content: {str(e)}"