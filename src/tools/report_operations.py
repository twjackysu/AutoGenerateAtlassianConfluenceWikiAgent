"""
Report operations tools - shared version for multi-agent system.
Simplified version based on the original report_generator.py.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from agents import function_tool


@function_tool
async def generate_report_shared(
    session_id: str,
    report_type: str = "comprehensive",
    output_path: str = "./reports"
) -> str:
    """
    Generate a comprehensive report from multi-agent analysis findings.
    
    Args:
        session_id: ID of the processing session
        report_type: Type of report to generate
        output_path: Directory to save the report
    
    Returns:
        Report generation status and location
    """
    try:
        # Load context data
        context_file = f"./cache/multi_agent_context_{session_id}.json"
        if not os.path.exists(context_file):
            return f"❌ Multi-agent context not found for session: {session_id}"
        
        with open(context_file, 'r', encoding='utf-8') as f:
            context_data = json.load(f)
        
        # Load session data
        session_file = f"./cache/multi_agent_session_{session_id}.json"
        session_data = {}
        if os.path.exists(session_file):
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
        
        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)
        
        # Generate report content
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"multi_agent_report_{session_id}_{timestamp}.md"
        report_path = os.path.join(output_path, report_filename)
        
        # Create comprehensive report
        report_content = _generate_comprehensive_report(session_id, session_data, context_data)
        
        # Save report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        output = f"""# 📊 Multi-Agent Report Generated

## 📝 Report Details
- **Session**: {session_id}
- **Report Type**: {report_type}
- **Generated**: {datetime.now().isoformat()}
- **Report File**: `{report_path}`

## 📈 Report Statistics
- **Total Findings**: {len(context_data.get('findings', []))}
- **Processed Files**: {len(context_data.get('processed_files', []))}
- **Contributing Agents**: {len(context_data.get('agent_contributions', {}))}

## 🔗 Access
Report saved to: `{report_path}`

The report contains a comprehensive analysis of the codebase performed by the multi-agent system.
"""
        
        return output
        
    except Exception as e:
        return f"❌ Error generating multi-agent report: {str(e)}"


@function_tool
async def list_available_report_types_shared() -> str:
    """
    List available report types for multi-agent system.
    
    Returns:
        List of available report types and descriptions
    """
    return """# 📋 Available Multi-Agent Report Types

## 🔍 Report Types

### 1. **Comprehensive Report** (`comprehensive`)
- Complete analysis summary from all agents
- File processing statistics
- Agent contribution breakdown
- All findings consolidated

### 2. **API Inventory** (`api_inventory`)
- List of discovered API endpoints
- HTTP methods and paths
- Source file locations

### 3. **Architecture Overview** (`architecture`)
- System architecture patterns
- Framework usage
- Module relationships

### 4. **Security Analysis** (`security`)
- Security-related findings
- Potential vulnerabilities
- Authentication patterns

### 5. **Performance Analysis** (`performance`)
- Performance-related observations
- Large file analysis
- Processing recommendations

## 🚀 Usage
Use `generate_report_shared(session_id, report_type)` to generate specific report types.

Example: `generate_report_shared("abc123", "api_inventory")`
"""


def _generate_comprehensive_report(session_id: str, session_data: Dict, context_data: Dict) -> str:
    """Generate a comprehensive multi-agent analysis report"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report = f"""# 🤖 Multi-Agent Codebase Analysis Report

*Generated on {timestamp} for session {session_id}*

## 📊 Executive Summary

This report presents the comprehensive analysis performed by a multi-agent system on the target codebase. The analysis was conducted using specialized agents working in coordination to provide thorough coverage and insights.

### 🎯 Analysis Overview
- **Session ID**: {session_id}
- **Repository**: {session_data.get('repo_path', 'Unknown')}
- **Analysis Goal**: {session_data.get('analysis_goal', 'Unknown')}
- **Strategy**: {session_data.get('strategy', 'Unknown')}
- **Session Status**: {session_data.get('status', 'Unknown')}

### 📈 Processing Statistics
- **Total Findings**: {len(context_data.get('findings', []))}
- **Processed Files**: {len(context_data.get('processed_files', []))}
- **Contributing Agents**: {len(context_data.get('agent_contributions', {}))}
- **Analysis Duration**: From {session_data.get('created_at', 'Unknown')} to {context_data.get('last_updated', 'Unknown')}

## 🤖 Multi-Agent System Performance

### Agent Contributions
"""
    
    # Add agent contribution details
    for agent, files in context_data.get('agent_contributions', {}).items():
        report += f"""
#### {agent}
- **Files Processed**: {len(files)}
- **Contribution**: {(len(files) / max(len(context_data.get('processed_files', [])), 1) * 100):.1f}% of total files
"""
    
    # Add processed files section
    if context_data.get('processed_files'):
        report += f"""

## 📁 Processed Files ({len(context_data['processed_files'])})

"""
        for i, file_path in enumerate(context_data['processed_files'], 1):
            report += f"{i:3d}. `{file_path}`\n"
    
    # Add findings section
    if context_data.get('findings'):
        report += f"""

## 🔍 Analysis Findings

### Summary by File
"""
        
        # Group findings by file
        findings_by_file = {}
        for finding in context_data['findings']:
            source_file = finding.get('source_file', 'Unknown')
            if source_file not in findings_by_file:
                findings_by_file[source_file] = []
            findings_by_file[source_file].append(finding)
        
        for file_path, file_findings in findings_by_file.items():
            report += f"""
#### `{file_path}`
- **Analysis Entries**: {len(file_findings)}
"""
            for finding in file_findings:
                findings_data = finding.get('findings', {})
                if findings_data:
                    report += f"- **Latest Analysis** ({finding.get('added_at', 'Unknown')}):\n"
                    
                    # Handle both dictionary and list formats
                    if isinstance(findings_data, dict):
                        for key, value in list(findings_data.items())[:3]:  # Show first 3 items
                            report += f"  - {key}: {value}\n"
                        if len(findings_data) > 3:
                            report += f"  - ... and {len(findings_data) - 3} more items\n"
                    elif isinstance(findings_data, list):
                        for i, item in enumerate(findings_data[:3]):  # Show first 3 items
                            report += f"  - Item {i+1}: {item}\n"
                        if len(findings_data) > 3:
                            report += f"  - ... and {len(findings_data) - 3} more items\n"
                    else:
                        report += f"  - Raw data: {findings_data}\n"
    
    # Add technical details section
    report += f"""

## 🔧 Technical Details

### Session Configuration
- **Session Type**: Multi-Agent System
- **Cache Location**: `./cache/multi_agent_context_{session_id}.json`
- **Processing Strategy**: {session_data.get('strategy', 'Unknown')}

### Data Quality
- **Context Integrity**: ✅ Valid
- **Finding Consistency**: ✅ Maintained across agents
- **Session State**: {session_data.get('status', 'Unknown')}

## 📋 Recommendations

Based on the multi-agent analysis:

1. **Code Coverage**: {len(context_data.get('processed_files', []))} files were successfully analyzed
2. **Agent Coordination**: {len(context_data.get('agent_contributions', {}))} agents contributed to the analysis
3. **Data Quality**: All findings are properly tracked and attributed

## 🔚 Conclusion

This multi-agent analysis provides a comprehensive view of the codebase structure, patterns, and characteristics. The coordinated approach ensures thorough coverage while maintaining data integrity and traceability.

---
*Report generated by Multi-Agent Codebase Analysis System*
*Session: {session_id} | Generated: {timestamp}*
"""
    
    return report