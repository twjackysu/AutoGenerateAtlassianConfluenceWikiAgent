import os
import re
import fnmatch
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from agents import function_tool
from .analysis_helpers import (
    get_architecture_analysis,
    get_data_sources_analysis,
    get_dependencies_analysis,
    get_overview_analysis
)


@function_tool
async def analyze_codebase_smart(
    repo_path: str,
    analysis_focus: str = "comprehensive",
    output_dir: str = None
) -> str:
    """
    Intelligently analyze a codebase, automatically determining if chunking is needed based on size.
    
    Args:
        repo_path: Path to the repository
        analysis_focus: Focus area ('architecture', 'data_sources', 'dependencies', 'overview', 'comprehensive')
        output_dir: Directory to save markdown files (optional, defaults to './generated_docs')
    
    Returns:
        Markdown documentation of the analysis and file save status
    """
    try:
        if not os.path.exists(repo_path):
            return f"## Error\nRepository path does not exist: {repo_path}"
        
        # Get all relevant files and assess size
        files = []
        total_size = 0
        
        for root, dirs, file_names in os.walk(repo_path):
            # Skip common directories that don't need analysis
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build']]
            
            for file_name in file_names:
                if file_name.endswith(('.py', '.js', '.ts', '.java', '.go', '.php', '.cpp', '.c', '.rs', '.rb', '.cs')):
                    file_path = os.path.join(root, file_name)
                    files.append(file_path)
                    try:
                        total_size += os.path.getsize(file_path)
                    except:
                        pass
        
        repo_name = os.path.basename(repo_path)
        
        # Determine analysis strategy based on size
        file_count = len(files)
        
        if file_count == 0:
            return f"# {repo_name} Analysis\n\n⚠️ No source code files found for analysis."
        
        # Auto-determine analysis approach
        if file_count <= 20 and total_size < 500000:  # Small project
            markdown_content = _analyze_small_project(files, repo_path, analysis_focus)
        elif file_count <= 100 and total_size < 2000000:  # Medium project  
            markdown_content = _analyze_medium_project(files, repo_path, analysis_focus)
        else:  # Large project - need summary approach
            markdown_content = _analyze_large_project(files, repo_path, analysis_focus)
        
        # Save to file if output_dir is specified
        if output_dir:
            file_path = _save_markdown_to_file(markdown_content, repo_name, analysis_focus, output_dir)
            return f"{markdown_content}\n\n---\n\n📁 **File saved**: {file_path}"
        else:
            return markdown_content
            
    except Exception as e:
        return f"## Error in Analysis\n{str(e)}"


def _save_markdown_to_file(content: str, repo_name: str, focus: str, output_dir: str) -> str:
    """Save markdown content to a file"""
    try:
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{repo_name}_{focus}_{timestamp}.md"
        file_path = os.path.join(output_dir, filename)
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    except Exception as e:
        return f"Error saving file: {str(e)}"


def _analyze_small_project(files: List[str], repo_path: str, focus: str) -> str:
    """Analyze small projects comprehensively"""
    
    repo_name = os.path.basename(repo_path)
    markdown = f"# {repo_name} - Complete Analysis\n\n"
    markdown += f"📊 **Project Size**: {len(files)} files (Small project - comprehensive analysis)\n\n"
    
    # Comprehensive analysis for small projects
    if focus in ["comprehensive", "architecture"]:
        markdown += get_architecture_analysis(files, repo_path)
    
    if focus in ["comprehensive", "data_sources"]:
        markdown += get_data_sources_analysis(files, repo_path)
    
    if focus in ["comprehensive", "dependencies"]:
        markdown += get_dependencies_analysis(files, repo_path)
    
    if focus in ["comprehensive", "overview"]:
        markdown += get_overview_analysis(files, repo_path)
    
    return markdown


def _analyze_medium_project(files: List[str], repo_path: str, focus: str) -> str:
    """Analyze medium projects with focused approach"""
    
    repo_name = os.path.basename(repo_path)
    markdown = f"# {repo_name} - Focused Analysis\n\n"
    markdown += f"📊 **Project Size**: {len(files)} files (Medium project - focused analysis)\n\n"
    
    # Focused analysis for medium projects
    if focus == "architecture":
        markdown += get_architecture_analysis(files, repo_path)
    elif focus == "data_sources":
        markdown += get_data_sources_analysis(files, repo_path)
    elif focus == "dependencies":
        markdown += get_dependencies_analysis(files, repo_path)
    else:  # comprehensive or overview
        markdown += get_overview_analysis(files, repo_path)
        markdown += "\n---\n\n"
        markdown += "💡 **Note**: For detailed analysis of this medium-sized project, request specific focus areas:\n"
        markdown += "- Architecture analysis\n- Data sources analysis\n- Dependencies analysis\n\n"
    
    return markdown


def _analyze_large_project(files: List[str], repo_path: str, focus: str) -> str:
    """Analyze large projects with summary approach"""
    
    repo_name = os.path.basename(repo_path)
    markdown = f"# {repo_name} - Summary Analysis\n\n"
    markdown += f"📊 **Project Size**: {len(files)} files (Large project - summary approach)\n\n"
    
    # High-level summary for large projects
    markdown += get_overview_analysis(files, repo_path)
    
    markdown += "\n---\n\n"
    markdown += "## 🎯 Recommended Next Steps\n\n"
    markdown += "This is a large project. For detailed analysis, consider:\n\n"
    markdown += "1. **Focus on specific directories**: Analyze key modules separately\n"
    markdown += "2. **Targeted analysis**: Request analysis of specific aspects:\n"
    markdown += "   - `analyze_codebase_smart('./path', 'architecture')`\n"
    markdown += "   - `analyze_codebase_smart('./path', 'data_sources')`\n"
    markdown += "   - `analyze_codebase_smart('./path', 'dependencies')`\n\n"
    
    # Show directory structure to help with targeted analysis
    markdown += "### 📁 Directory Structure (for targeted analysis)\n\n"
    dirs = set()
    for file_path in files[:50]:  # Sample first 50 files
        rel_path = os.path.relpath(file_path, repo_path)
        dirs.add(os.path.dirname(rel_path))
    
    for directory in sorted(dirs):
        if directory:
            markdown += f"- `{directory}/`\n"
    
    return markdown