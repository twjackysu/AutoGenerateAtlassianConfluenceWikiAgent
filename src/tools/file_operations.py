"""
File operations tools - shared version for multi-agent system.
Combines functionality from file_scanner.py and file_reader.py.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Set, Union, Tuple
from dataclasses import dataclass
from agents import function_tool
from atlassian import Confluence
import requests
from datetime import datetime


@dataclass
class FileInfo:
    """Information about a code file"""
    path: str
    size: int
    language: str
    estimated_tokens: int
    modified_time: float
    relative_path: str


@dataclass
class FileChunk:
    """A chunk of file content with metadata"""
    content: str
    chunk_index: int
    total_chunks: int
    start_line: int
    end_line: int
    estimated_tokens: int
    chunk_type: str  # 'function', 'class', 'logical_block', 'raw'


@dataclass
class ReadResult:
    """Result of reading a file"""
    file_path: str
    chunks: List[FileChunk]
    total_lines: int
    file_size: int
    language: str
    success: bool
    error_message: Optional[str] = None


# Import constants and helper functions from original modules
LANGUAGE_EXTENSIONS = {
    '.py': 'Python',
    '.cpp': 'C++', '.cc': 'C++', '.cxx': 'C++',
    '.c': 'C', '.h': 'C/C++', '.hpp': 'C++',
    '.java': 'Java',
    '.cs': 'C#',
    '.js': 'JavaScript', '.jsx': 'JavaScript',
    '.ts': 'TypeScript', '.tsx': 'TypeScript',
    '.sql': 'SQL',
    '.go': 'Go',
    '.php': 'PHP',
    '.rb': 'Ruby',
    '.rs': 'Rust',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
    '.pl': 'Perl',
    '.sh': 'Shell', '.bash': 'Shell',
    '.ps1': 'PowerShell',
    '.yaml': 'YAML', '.yml': 'YAML',
    '.json': 'JSON',
    '.xml': 'XML',
    '.html': 'HTML',
    '.css': 'CSS', '.scss': 'SCSS', '.sass': 'SASS',
    '.vue': 'Vue',
    '.svelte': 'Svelte'
}

SKIP_DIRECTORIES = {
    '.git', '.svn', '.hg',
    '__pycache__', '.pytest_cache',
    'node_modules', '.npm',
    '.venv', 'venv', 'env',
    'build', 'dist', 'out',
    '.idea', '.vscode',
    'bin', 'obj',
    'target', '.gradle',
    'vendor', 'deps',
    '.next', '.nuxt',
    'coverage', '.nyc_output',
    'logs', 'log',
    'tmp', 'temp',
    '.DS_Store'
}

SKIP_FILES = {
    '.gitignore', '.gitattributes',
    '.dockerignore', 'Dockerfile',
    'package-lock.json', 'yarn.lock',
    'pipfile.lock', 'poetry.lock',
    'composer.lock', 'gemfile.lock',
    '.env', '.env.local', '.env.example',
    'readme.md', 'license', 'changelog.md'
}


def estimate_tokens(content_or_size: Union[str, int]) -> int:
    """Estimate token count based on content or file size"""
    if isinstance(content_or_size, str):
        return len(content_or_size) // 4
    else:
        return content_or_size // 4


def should_skip_directory(dir_name: str) -> bool:
    """Check if directory should be skipped"""
    return dir_name.lower() in SKIP_DIRECTORIES or dir_name.startswith('.')


def should_skip_file(file_name: str) -> bool:
    """Check if file should be skipped"""
    return (file_name.lower() in SKIP_FILES or 
            file_name.startswith('.') or
            file_name.endswith('.min.js') or
            file_name.endswith('.bundle.js'))


def detect_language(file_path: str) -> str:
    """Detect programming language from file extension"""
    ext = Path(file_path).suffix.lower()
    return LANGUAGE_EXTENSIONS.get(ext, 'Unknown')


@function_tool
async def scan_repository_extensions_shared(
    repo_path: str,
    include_config: bool = True
) -> str:
    """
    Scan repository to discover all file extensions present.
    Use this before list_all_code_files_shared to understand what languages are in the repo.
    
    Args:
        repo_path: Path to the repository root
        include_config: Whether to include configuration files
    
    Returns:
        Summary of all extensions found in the repository
    """
    try:
        # Check if this looks like a GitHub repo name and adjust path
        if not os.path.exists(repo_path):
            potential_repo_path = os.path.join("repos", repo_path)
            if os.path.exists(potential_repo_path):
                repo_path = potential_repo_path
            else:
                return f"❌ Error: Repository path does not exist: {repo_path} (also tried repos/{repo_path})"
        
        repo_path = os.path.abspath(repo_path)
        extension_counts = {}
        total_files = 0
        
        # Walk through directory tree
        for root, dirs, file_names in os.walk(repo_path):
            # Filter out directories to skip
            dirs[:] = [d for d in dirs if not should_skip_directory(d)]
            
            for file_name in file_names:
                # Skip unwanted files
                if should_skip_file(file_name):
                    continue
                
                file_ext = Path(file_name).suffix.lower()
                if file_ext:  # Only count files with extensions
                    extension_counts[file_ext] = extension_counts.get(file_ext, 0) + 1
                    total_files += 1
        
        # Categorize extensions
        code_extensions = {}
        config_extensions = {}
        other_extensions = {}
        
        for ext, count in extension_counts.items():
            language = LANGUAGE_EXTENSIONS.get(ext, 'Unknown')
            if ext in LANGUAGE_EXTENSIONS:
                code_extensions[ext] = {'count': count, 'language': language}
            elif ext in {'.yaml', '.yml', '.json', '.xml', '.toml', '.ini', '.cfg', '.conf'}:
                config_extensions[ext] = {'count': count, 'type': 'Configuration'}
            else:
                other_extensions[ext] = {'count': count, 'type': 'Other'}
        
        # Generate report
        output = f"""# 🔍 Repository Extension Scan
        
## 📊 Scan Summary
- **Repository**: `{repo_path}`
- **Total Files Scanned**: {total_files:,}
- **Unique Extensions**: {len(extension_counts)}

## 💻 Code Files Found
"""
        
        if code_extensions:
            for ext, info in sorted(code_extensions.items(), key=lambda x: x[1]['count'], reverse=True):
                output += f"- **{ext}** ({info['language']}): {info['count']} files\n"
        else:
            output += "- No recognized code files found\n"
        
        if config_extensions and include_config:
            output += f"""
## ⚙️ Configuration Files Found
"""
            for ext, info in sorted(config_extensions.items(), key=lambda x: x[1]['count'], reverse=True):
                output += f"- **{ext}** ({info['type']}): {info['count']} files\n"
        
        if other_extensions:
            output += f"""
## 📄 Other Files Found
"""
            for ext, info in sorted(other_extensions.items(), key=lambda x: x[1]['count'], reverse=True):
                output += f"- **{ext}** ({info['type']}): {info['count']} files\n"
        
        # Provide recommendations
        recommended_extensions = list(code_extensions.keys())
        if include_config:
            recommended_extensions.extend(config_extensions.keys())
        
        output += f"""
## 💡 Recommendations
**Suggested extensions for analysis**: {recommended_extensions}

**Next step**: Use `list_all_code_files_shared(repo_path, extensions={recommended_extensions})` for targeted analysis.
"""
        
        return output
        
    except Exception as e:
        return f"❌ Error scanning repository extensions: {str(e)}"


@function_tool
async def list_all_code_files_shared(
    repo_path: str,
    extensions: Optional[List[str]] = None,
    include_config: bool = True,
    max_file_size: int = 10 * 1024 * 1024  # 10MB default limit
) -> str:
    """
    Recursively list all code files in a repository with metadata.
    Shared version for multi-agent system.
    
    Args:
        repo_path: Path to the repository root
        extensions: List of specific extensions to include (e.g. ['.py', '.js']). 
                   If None, includes all supported languages
        include_config: Whether to include configuration files (yaml, json, etc.)
        max_file_size: Maximum file size to include (bytes)
    
    Returns:
        JSON string with file information and summary statistics
    """
    try:
        # Check if this looks like a GitHub repo name and adjust path
        if not os.path.exists(repo_path):
            # Try with repos/ prefix for GitHub repositories
            potential_repo_path = os.path.join("repos", repo_path)
            if os.path.exists(potential_repo_path):
                repo_path = potential_repo_path
            else:
                return f"❌ Error: Repository path does not exist: {repo_path} (also tried repos/{repo_path})"
        
        repo_path = os.path.abspath(repo_path)
        files: List[FileInfo] = []
        total_size = 0
        language_counts = {}
        skipped_files = []
        
        # Determine which extensions to include
        target_extensions = set()
        if extensions:
            target_extensions = {ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                               for ext in extensions}
        else:
            target_extensions = set(LANGUAGE_EXTENSIONS.keys())
            if not include_config:
                # Remove config file extensions
                config_exts = {'.yaml', '.yml', '.json', '.xml'}
                target_extensions -= config_exts
        
        # Walk through directory tree
        for root, dirs, file_names in os.walk(repo_path):
            # Filter out directories to skip
            dirs[:] = [d for d in dirs if not should_skip_directory(d)]
            
            for file_name in file_names:
                file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(file_path, repo_path)
                
                # Skip unwanted files
                if should_skip_file(file_name):
                    continue
                
                # Check file extension
                file_ext = Path(file_name).suffix.lower()
                if file_ext not in target_extensions:
                    continue
                
                try:
                    # Get file stats
                    stat = os.stat(file_path)
                    file_size = stat.st_size
                    
                    # Skip files that are too large
                    if file_size > max_file_size:
                        skipped_files.append({
                            'path': relative_path,
                            'reason': f'File too large ({file_size:,} bytes)',
                            'size': file_size
                        })
                        continue
                    
                    # Skip empty files
                    if file_size == 0:
                        continue
                    
                    language = detect_language(file_name)
                    estimated_tokens = estimate_tokens(file_size)
                    
                    file_info = FileInfo(
                        path=file_path,
                        size=file_size,
                        language=language,
                        estimated_tokens=estimated_tokens,
                        modified_time=stat.st_mtime,
                        relative_path=relative_path
                    )
                    
                    files.append(file_info)
                    total_size += file_size
                    language_counts[language] = language_counts.get(language, 0) + 1
                    
                except (OSError, PermissionError) as e:
                    skipped_files.append({
                        'path': relative_path,
                        'reason': f'Access error: {str(e)}',
                        'size': 0
                    })
                    continue
        
        # Sort files by size (largest first) for better batch planning
        files.sort(key=lambda x: x.size, reverse=True)
        
        # Generate summary report
        total_estimated_tokens = sum(f.estimated_tokens for f in files)
        
        # Create file list for output
        file_list = [
            {
                'relative_path': f.relative_path,
                'full_path': f.path,  # Include full path for reading
                'size': f.size,
                'language': f.language,
                'estimated_tokens': f.estimated_tokens,
                'size_mb': round(f.size / (1024 * 1024), 2)
            }
            for f in files
        ]
        
        # Build summary
        summary = {
            'repository_path': repo_path,
            'total_files': len(files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'total_estimated_tokens': total_estimated_tokens,
            'language_distribution': language_counts,
            'largest_files': [
                {
                    'path': f.relative_path,
                    'size_mb': round(f.size / (1024 * 1024), 2),
                    'language': f.language
                }
                for f in files[:10]  # Top 10 largest files
            ],
            'skipped_files_count': len(skipped_files),
            'skipped_files': skipped_files[:20] if skipped_files else [],  # Show first 20 skipped
            'processing_recommendations': _generate_processing_recommendations(files, total_estimated_tokens)
        }
        
        result = {
            'summary': summary,
            'files': file_list
        }
        
        # Convert to formatted string output
        output = _format_file_listing_output(result)
        return output
        
    except Exception as e:
        return f"❌ Error scanning repository: {str(e)}"


def _generate_processing_recommendations(files: List[FileInfo], total_tokens: int) -> Dict:
    """Generate recommendations for processing strategy"""
    recommendations = {
        'suggested_batch_size': 'small',
        'estimated_batches': 1,
        'processing_strategy': 'single_pass',
        'warnings': []
    }
    
    # Determine batch strategy based on size and token count
    if total_tokens > 100000:  # Very large codebase
        recommendations['suggested_batch_size'] = 'small'
        recommendations['estimated_batches'] = max(10, total_tokens // 10000)
        recommendations['processing_strategy'] = 'multi_batch_with_context'
        recommendations['warnings'].append('Large codebase detected - consider targeted analysis')
    elif total_tokens > 50000:  # Medium codebase
        recommendations['suggested_batch_size'] = 'medium'
        recommendations['estimated_batches'] = max(5, total_tokens // 20000)
        recommendations['processing_strategy'] = 'multi_batch'
    else:  # Small codebase
        recommendations['suggested_batch_size'] = 'large'
        recommendations['estimated_batches'] = 1
        recommendations['processing_strategy'] = 'single_pass'
    
    # Check for very large individual files
    large_files = [f for f in files if f.estimated_tokens > 5000]
    if large_files:
        recommendations['warnings'].append(f'{len(large_files)} large files may need chunking')
    
    return recommendations


def _format_file_listing_output(result: Dict) -> str:
    """Format the file listing result as markdown"""
    summary = result['summary']
    files = result['files']
    
    output = f"""# 📁 Code Repository Analysis (Shared Tools)

## 📊 Summary Statistics
- **Repository**: `{summary['repository_path']}`
- **Total Files**: {summary['total_files']:,}
- **Total Size**: {summary['total_size_mb']:.1f} MB ({summary['total_size_bytes']:,} bytes)
- **Estimated Tokens**: {summary['total_estimated_tokens']:,}

## 🌐 Language Distribution
"""
    
    for language, count in sorted(summary['language_distribution'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / summary['total_files']) * 100
        output += f"- **{language}**: {count} files ({percentage:.1f}%)\n"
    
    output += f"""

## 📈 Processing Recommendations
- **Suggested Strategy**: {summary['processing_recommendations']['processing_strategy']}
- **Estimated Batches**: {summary['processing_recommendations']['estimated_batches']}
- **Batch Size**: {summary['processing_recommendations']['suggested_batch_size']}
"""
    
    if summary['processing_recommendations']['warnings']:
        output += "\n### ⚠️ Warnings\n"
        for warning in summary['processing_recommendations']['warnings']:
            output += f"- {warning}\n"
    
    if summary['largest_files']:
        output += f"\n## 📏 Largest Files\n"
        for file_info in summary['largest_files']:
            output += f"- `{file_info['path']}` ({file_info['size_mb']:.1f} MB, {file_info['language']})\n"
    
    if summary['skipped_files_count'] > 0:
        output += f"\n## ⏭️ Skipped Files\n"
        output += f"Total skipped: {summary['skipped_files_count']} files\n\n"
        for skipped in summary['skipped_files']:
            output += f"- `{skipped['path']}`: {skipped['reason']}\n"
    
    output += f"\n## 📄 Complete File Listing\n"
    output += f"**Note**: To read files, use repository path + relative path with read_file_smart_shared()\n\n"
    for i, file_info in enumerate(files, 1):
        output += f"{i:3d}. `{file_info['relative_path']}` "
        output += f"({file_info['size_mb']:.2f} MB, {file_info['estimated_tokens']:,} tokens, {file_info['language']})\n"
    
    return output


@function_tool
async def read_file_smart_shared(
    file_path: str,
    chunk_size: Union[str, int] = "auto",
    chunk_index: Optional[int] = None,
    max_tokens_per_chunk: int = 2000,
    repo_path: Optional[str] = None
) -> str:
    """
    Intelligently read a file with smart chunking strategies.
    Shared version for multi-agent system.
    
    Args:
        file_path: Path to the file to read (can be relative or absolute)
        chunk_size: Either "auto" for intelligent chunking, or an integer for fixed-size chunks
        chunk_index: If specified, return only this chunk (0-based). If None, return all chunks
        max_tokens_per_chunk: Maximum tokens per chunk when using auto chunking
        repo_path: Optional repository root path to combine with relative file_path
    
    Returns:
        Formatted string with file content and metadata
    """
    try:
        # Handle relative paths by combining with repo_path
        if repo_path and not os.path.isabs(file_path):
            file_path = os.path.join(repo_path, file_path)
        
        # Check if this looks like a GitHub repo file and adjust path
        if not os.path.exists(file_path):
            # Try with repos/ prefix for GitHub repositories
            potential_file_path = os.path.join("repos", file_path)
            if os.path.exists(potential_file_path):
                file_path = potential_file_path
            else:
                return f"❌ Error: File does not exist: {file_path} (also tried repos/{file_path})"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return f"⚠️ Warning: File is empty: {file_path}"
        
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            return f"❌ Error: File too large ({file_size / (1024*1024):.1f} MB): {file_path}"
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin1', errors='ignore') as f:
                content = f.read()
        
        if not content.strip():
            return f"⚠️ Warning: File appears to be empty or contains only whitespace: {file_path}"
        
        # Detect language and prepare chunking
        language = detect_language(file_path).lower()
        total_lines = len(content.split('\n'))
        
        # Create chunks (simplified version for now)
        chunks = []
        if chunk_size == "auto":
            # Simple line-based chunking for shared version
            lines = content.split('\n')
            lines_per_chunk = 100  # Default chunk size
            
            for i in range(0, len(lines), lines_per_chunk):
                chunk_lines = lines[i:i + lines_per_chunk]
                chunk_content = '\n'.join(chunk_lines)
                
                chunk = FileChunk(
                    content=chunk_content,
                    chunk_index=i // lines_per_chunk,
                    total_chunks=(len(lines) + lines_per_chunk - 1) // lines_per_chunk,
                    start_line=i + 1,
                    end_line=min(i + lines_per_chunk, len(lines)),
                    estimated_tokens=estimate_tokens(chunk_content),
                    chunk_type="code_block"
                )
                chunks.append(chunk)
        else:
            # Fixed-size chunking by lines
            lines = content.split('\n')
            lines_per_chunk = int(chunk_size) if isinstance(chunk_size, (int, str)) and str(chunk_size).isdigit() else 100
            
            for i in range(0, len(lines), lines_per_chunk):
                chunk_lines = lines[i:i + lines_per_chunk]
                chunk_content = '\n'.join(chunk_lines)
                
                chunk = FileChunk(
                    content=chunk_content,
                    chunk_index=i // lines_per_chunk,
                    total_chunks=(len(lines) + lines_per_chunk - 1) // lines_per_chunk,
                    start_line=i + 1,
                    end_line=min(i + lines_per_chunk, len(lines)),
                    estimated_tokens=estimate_tokens(chunk_content),
                    chunk_type="raw_chunk"
                )
                chunks.append(chunk)
        
        # Create result
        result = ReadResult(
            file_path=file_path,
            chunks=chunks,
            total_lines=total_lines,
            file_size=file_size,
            language=language,
            success=True
        )
        
        # Return specific chunk if requested
        if chunk_index is not None:
            if 0 <= chunk_index < len(chunks):
                selected_chunk = chunks[chunk_index]
                return _format_single_chunk_output(result, selected_chunk)
            else:
                return f"❌ Error: Chunk index {chunk_index} out of range (0-{len(chunks)-1})"
        
        # Return all chunks overview
        return _format_full_file_output(result)
        
    except Exception as e:
        return f"❌ Error reading file {file_path}: {str(e)}"


def _format_single_chunk_output(result: ReadResult, chunk: FileChunk) -> str:
    """Format output for a single chunk"""
    output = f"""# 📄 File Chunk: {os.path.basename(result.file_path)} (Shared Tools)

## 📊 Chunk Information
- **File**: `{result.file_path}`
- **Language**: {result.language}
- **Chunk**: {chunk.chunk_index + 1} of {chunk.total_chunks}
- **Lines**: {chunk.start_line}-{chunk.end_line} (of {result.total_lines} total)
- **Chunk Type**: {chunk.chunk_type}
- **Estimated Tokens**: {chunk.estimated_tokens:,}
- **File Size**: {result.file_size:,} bytes

## 📝 Content

```{result.language}
{chunk.content}
```
"""
    return output


def _format_full_file_output(result: ReadResult) -> str:
    """Format output for complete file overview"""
    relative_path = os.path.basename(result.file_path)
    
    output = f"""# 📄 File Analysis Overview: {relative_path} (Shared Tools)

## 📊 File Information
- **Full Path**: `{result.file_path}`
- **Language**: {result.language}
- **Total Lines**: {result.total_lines:,}
- **File Size**: {result.file_size:,} bytes ({result.file_size / 1024:.1f} KB)
- **Total Chunks**: {len(result.chunks)}
- **Total Estimated Tokens**: {sum(c.estimated_tokens for c in result.chunks):,}

## 🧩 Chunk Overview
"""
    
    for i, chunk in enumerate(result.chunks):
        output += f"**Chunk {i+1}** ({chunk.chunk_type}): Lines {chunk.start_line}-{chunk.end_line}, {chunk.estimated_tokens:,} tokens\n"
    
    output += f"""

## 🔄 How to Access Content
To read the actual content, use `read_file_smart_shared()` with specific chunk indices:

"""
    
    for i, chunk in enumerate(result.chunks):
        output += f"- **Chunk {i}**: `read_file_smart_shared(\"{result.file_path}\", chunk_index={i})` - {chunk.chunk_type} ({chunk.estimated_tokens:,} tokens)\n"
    
    # Include preview if not too large
    if result.chunks and result.chunks[0].estimated_tokens < 1000:
        first_chunk = result.chunks[0]
        preview_lines = first_chunk.content.split('\n')[:15]
        preview_content = '\n'.join(preview_lines)
        if len(first_chunk.content.split('\n')) > 15:
            preview_content += f"\n... ({len(first_chunk.content.split('\n')) - 15} more lines in this chunk)"
        
        output += f"""

## 📝 Content Preview (First Chunk)

```{result.language}
{preview_content}
```

⚠️ **Note**: Use `read_file_smart_shared()` with `chunk_index` parameter to read specific chunks.
"""
    
    return output


@function_tool
async def save_report_file_shared(
    content: str,
    filename: str,
    directory: str = "./test_reports/multi_agent/"
) -> str:
    """
    Save a report file to the specified directory.
    
    Args:
        content: The content to write to the file
        filename: The name of the file (with extension)
        directory: The directory to save the file in (default: ./test_reports/multi_agent/)
    
    Returns:
        Status message with file path
    """
    try:
        from datetime import datetime
        
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Construct full file path
        file_path = os.path.join(directory, filename)
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        return f"""✅ **Report Saved Successfully**

📁 **File Location**: `{file_path}`
📊 **File Size**: {file_size:,} bytes
📝 **Content Length**: {len(content):,} characters
🕐 **Saved**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The report has been saved and is ready for access.
"""
        
    except Exception as e:
        return f"❌ **Error saving report**: {str(e)}"


def _get_confluence_client() -> Optional[Confluence]:
    """
    Create and return a Confluence client using environment variables.
    
    Required environment variables:
    - CONFLUENCE_URL: Your Atlassian instance URL (e.g., https://your-domain.atlassian.net)
    - CONFLUENCE_EMAIL: Your email address
    - CONFLUENCE_API_TOKEN: Your API token
    
    Returns:
        Confluence client or None if configuration is missing
    """
    try:
        url = os.getenv('CONFLUENCE_URL')
        email = os.getenv('CONFLUENCE_EMAIL')
        token = os.getenv('CONFLUENCE_API_TOKEN')
        
        if not all([url, email, token]):
            missing = []
            if not url: missing.append('CONFLUENCE_URL')
            if not email: missing.append('CONFLUENCE_EMAIL')
            if not token: missing.append('CONFLUENCE_API_TOKEN')
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")
        
        confluence = Confluence(
            url=url,
            username=email,
            password=token,
            cloud=True
        )
        
        # Test connection
        confluence.get_all_spaces(limit=1)
        return confluence
        
    except Exception as e:
        print(f"Failed to initialize Confluence client: {str(e)}")
        return None


def _convert_markdown_to_confluence_storage(markdown_content: str) -> str:
    """
    Convert Markdown content to Confluence Storage Format.
    
    Args:
        markdown_content: Markdown content string
        
    Returns:
        Confluence storage format string
    """
    # Basic Markdown to Confluence conversion
    # This is a simplified converter - for production use, consider using a proper converter
    content = markdown_content
    
    # Headers
    content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', content, flags=re.MULTILINE)
    content = re.sub(r'^##### (.*?)$', r'<h5>\1</h5>', content, flags=re.MULTILINE)
    content = re.sub(r'^###### (.*?)$', r'<h6>\1</h6>', content, flags=re.MULTILINE)
    
    # Bold and Italic
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
    
    # Code blocks
    content = re.sub(r'```(\w+)?\n(.*?)\n```', r'<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">\1</ac:parameter><ac:plain-text-body><![CDATA[\2]]></ac:plain-text-body></ac:structured-macro>', content, flags=re.DOTALL)
    
    # Inline code
    content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)
    
    # Lists (simplified)
    content = re.sub(r'^- (.*?)$', r'<ul><li>\1</li></ul>', content, flags=re.MULTILINE)
    content = re.sub(r'^(\d+)\. (.*?)$', r'<ol><li>\2</li></ol>', content, flags=re.MULTILINE)
    
    # Line breaks
    content = content.replace('\n\n', '<br/><br/>')
    content = content.replace('\n', '<br/>')
    
    return content


@function_tool
async def search_confluence_spaces_shared(
    query: str = "",
    limit: int = 25
) -> str:
    """
    Search for Confluence spaces by name or key.
    
    Args:
        query: Search query (space name or key). If empty, returns all spaces.
        limit: Maximum number of spaces to return (default: 25)
    
    Returns:
        Formatted list of spaces with keys, names, and URLs
    """
    try:
        confluence = _get_confluence_client()
        if not confluence:
            return "❌ **Error**: Could not connect to Confluence. Please check your environment variables."
        
        # Get all spaces
        spaces = confluence.get_all_spaces(limit=limit)
        
        # Filter by query if provided
        if query:
            query_lower = query.lower()
            filtered_spaces = []
            for space in spaces:
                if (query_lower in space.get('name', '').lower() or 
                    query_lower in space.get('key', '').lower()):
                    filtered_spaces.append(space)
            spaces = filtered_spaces
        
        if not spaces:
            return f"📭 **No spaces found** matching query: '{query}'"
        
        output = f"""# 🏠 Confluence Spaces Found

## 📊 Search Results
- **Query**: "{query}" (showing {len(spaces)} results)
- **Total found**: {len(spaces)} spaces

## 📋 Space List
"""
        
        for space in spaces:
            space_key = space.get('key', 'N/A')
            space_name = space.get('name', 'Unnamed')
            space_type = space.get('type', 'Unknown')
            space_url = f"{os.getenv('CONFLUENCE_URL', '')}/spaces/{space_key}"
            
            output += f"""
### 🏷️ {space_name}
- **Key**: `{space_key}`
- **Type**: {space_type}
- **URL**: {space_url}
"""
        
        output += f"""

## 💡 Next Steps
To search for pages in a specific space, use:
`search_confluence_pages_shared(space_key="SPACE_KEY", query="your search")`

To get detailed information about a space, use the space key from above.
"""
        
        return output
        
    except Exception as e:
        return f"❌ **Error searching spaces**: {str(e)}"


@function_tool
async def search_confluence_pages_shared(
    space_key: str,
    query: str = "",
    limit: int = 25
) -> str:
    """
    Search for pages in a specific Confluence space.
    
    Args:
        space_key: The key of the space to search in
        query: Search query (page title or content). If empty, returns all pages in space.
        limit: Maximum number of pages to return (default: 25)
    
    Returns:
        Formatted list of pages with IDs, titles, and URLs
    """
    try:
        confluence = _get_confluence_client()
        if not confluence:
            return "❌ **Error**: Could not connect to Confluence. Please check your environment variables."
        
        # Get pages from space
        pages = confluence.get_all_pages_from_space(space_key, limit=limit)
        
        # Filter by query if provided
        if query:
            query_lower = query.lower()
            filtered_pages = []
            for page in pages:
                if query_lower in page.get('title', '').lower():
                    filtered_pages.append(page)
            pages = filtered_pages
        
        if not pages:
            return f"📭 **No pages found** in space '{space_key}' matching query: '{query}'"
        
        output = f"""# 📄 Confluence Pages Found

## 📊 Search Results
- **Space**: {space_key}
- **Query**: "{query}"
- **Results**: {len(pages)} pages found

## 📋 Page List
"""
        
        for page in pages:
            page_id = page.get('id', 'N/A')
            page_title = page.get('title', 'Untitled')
            page_url = f"{os.getenv('CONFLUENCE_URL', '')}/spaces/{space_key}/pages/{page_id}"
            
            output += f"""
### 📝 {page_title}
- **ID**: `{page_id}`
- **Space**: {space_key}
- **URL**: {page_url}
"""
        
        output += f"""

## 💡 Next Steps
To get detailed information about a page, use:
`get_confluence_page_info_shared(page_id="PAGE_ID")`

To update or create a page, use the page ID from above with:
`upload_to_confluence_shared(content="...", title="...", space_key="{space_key}", page_id="PAGE_ID")`
"""
        
        return output
        
    except Exception as e:
        return f"❌ **Error searching pages**: {str(e)}"


@function_tool
async def get_confluence_page_info_shared(
    page_id: str
) -> str:
    """
    Get detailed information about a specific Confluence page.
    
    Args:
        page_id: The ID of the page to get information about
    
    Returns:
        Detailed page information including title, space, content preview, and metadata
    """
    try:
        confluence = _get_confluence_client()
        if not confluence:
            return "❌ **Error**: Could not connect to Confluence. Please check your environment variables."
        
        # Get page details
        page = confluence.get_page_by_id(page_id, expand='body.storage,space,version,ancestors')
        
        if not page:
            return f"❌ **Page not found**: No page with ID '{page_id}'"
        
        page_title = page.get('title', 'Untitled')
        space_info = page.get('space', {})
        space_key = space_info.get('key', 'Unknown')
        space_name = space_info.get('name', 'Unknown')
        version_info = page.get('version', {})
        version_number = version_info.get('number', 'Unknown')
        
        # Get content preview
        body = page.get('body', {})
        storage = body.get('storage', {})
        content = storage.get('value', '')
        content_preview = content[:500] + "..." if len(content) > 500 else content
        
        # Get ancestors (parent pages)
        ancestors = page.get('ancestors', [])
        parent_path = " → ".join([ancestor.get('title', 'Unknown') for ancestor in ancestors])
        
        page_url = f"{os.getenv('CONFLUENCE_URL', '')}/spaces/{space_key}/pages/{page_id}"
        
        output = f"""# 📄 Confluence Page Details

## 📊 Page Information
- **Title**: {page_title}
- **ID**: `{page_id}`
- **Space**: {space_name} (`{space_key}`)
- **Version**: {version_number}
- **URL**: {page_url}

## 📂 Page Hierarchy
{f"**Path**: {parent_path} → {page_title}" if parent_path else "**Location**: Root level"}

## 📝 Content Preview
```html
{content_preview}
```

## 💡 Available Actions
- **Update this page**: Use `upload_to_confluence_shared(content="...", title="{page_title}", space_key="{space_key}", page_id="{page_id}")`
- **Create child page**: Use `upload_to_confluence_shared(content="...", title="New Page", space_key="{space_key}", parent_page_id="{page_id}")`
"""
        
        return output
        
    except Exception as e:
        return f"❌ **Error getting page info**: {str(e)}"


@function_tool
async def upload_to_confluence_shared(
    content: str,
    title: str,
    space_key: str,
    page_id: str = None,
    parent_page_id: str = None
) -> str:
    """
    Upload or update a report to Atlassian Confluence as a wiki page.
    
    Args:
        content: The markdown content to upload
        title: The title of the wiki page
        space_key: The Confluence space key
        page_id: If provided, update this existing page. If None, create new page.
        parent_page_id: If creating new page, set this as parent page ID
    
    Returns:
        Status message with page URL and details
    """
    try:
        confluence = _get_confluence_client()
        if not confluence:
            return "❌ **Error**: Could not connect to Confluence. Please check your environment variables."
        
        # Convert markdown to Confluence storage format
        confluence_content = _convert_markdown_to_confluence_storage(content)
        
        if page_id:
            # Update existing page
            try:
                current_page = confluence.get_page_by_id(page_id, expand='version')
                current_version = current_page.get('version', {}).get('number', 1)
                
                result = confluence.update_page(
                    page_id=page_id,
                    title=title,
                    body=confluence_content,
                    version_number=current_version + 1
                )
                
                page_url = f"{os.getenv('CONFLUENCE_URL', '')}/spaces/{space_key}/pages/{page_id}"
                
                return f"""✅ **Page Updated Successfully**

📄 **Page**: {title}
🆔 **Page ID**: {page_id}
🏠 **Space**: {space_key}
📊 **Content Size**: {len(content):,} characters
🔗 **URL**: {page_url}
📝 **Version**: {current_version + 1}
🕐 **Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The page has been updated and is now live on Confluence.
"""
                
            except Exception as e:
                return f"❌ **Error updating page**: {str(e)}"
        
        else:
            # Create new page
            try:
                result = confluence.create_page(
                    space=space_key,
                    title=title,
                    body=confluence_content,
                    parent_id=parent_page_id
                )
                
                new_page_id = result.get('id')
                page_url = f"{os.getenv('CONFLUENCE_URL', '')}/spaces/{space_key}/pages/{new_page_id}"
                
                return f"""✅ **Page Created Successfully**

📄 **Page**: {title}
🆔 **New Page ID**: {new_page_id}
🏠 **Space**: {space_key}
📊 **Content Size**: {len(content):,} characters
🔗 **URL**: {page_url}
{f"📂 **Parent Page ID**: {parent_page_id}" if parent_page_id else "📂 **Location**: Root level"}
🕐 **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The new page has been created and is now live on Confluence.
"""
                
            except Exception as e:
                return f"❌ **Error creating page**: {str(e)}"
        
    except Exception as e:
        return f"❌ **Error uploading to Confluence**: {str(e)}"


@function_tool
async def scan_files_by_pattern_shared(
    repo_path: str,
    filename_patterns: Optional[List[str]] = None,
    path_patterns: Optional[List[str]] = None,
    content_keywords: Optional[List[str]] = None,
    max_files: int = 1000
) -> str:
    """
    Smart file scanning that supports multiple search patterns beyond file extensions.
    Designed to help AnalysisAgent find files based on user requirements.
    
    Args:
        repo_path: Path to the repository root
        filename_patterns: List of filename glob patterns (e.g. ["*Dockerfile*", "Makefile", "*.config"])
        path_patterns: List of path glob patterns (e.g. ["src/controllers/*", "*/migrations/*"])
        content_keywords: List of keywords to search in file content (e.g. ["@RestController", "class.*Controller"])
        max_files: Maximum number of files to return (default: 1000)
    
    Returns:
        Formatted string with found files and metadata
    """
    try:
        import fnmatch
        import glob
        
        # Check if this looks like a GitHub repo name and adjust path
        if not os.path.exists(repo_path):
            potential_repo_path = os.path.join("repos", repo_path)
            if os.path.exists(potential_repo_path):
                repo_path = potential_repo_path
            else:
                return f"❌ Error: Repository path does not exist: {repo_path} (also tried repos/{repo_path})"
        
        repo_path = os.path.abspath(repo_path)
        found_files = []
        
        # 1. Search by filename patterns
        if filename_patterns:
            for pattern in filename_patterns:
                for root, dirs, files in os.walk(repo_path):
                    # Skip unwanted directories
                    dirs[:] = [d for d in dirs if not should_skip_directory(d)]
                    
                    for file_name in files:
                        if fnmatch.fnmatch(file_name, pattern):
                            file_path = os.path.join(root, file_name)
                            relative_path = os.path.relpath(file_path, repo_path)
                            
                            if should_skip_file(file_name):
                                continue
                                
                            try:
                                stat = os.stat(file_path)
                                found_files.append({
                                    'path': file_path,
                                    'relative_path': relative_path,
                                    'size': stat.st_size,
                                    'match_type': 'filename_pattern',
                                    'match_pattern': pattern,
                                    'language': detect_language(file_name),
                                    'modified_time': stat.st_mtime
                                })
                            except (OSError, PermissionError):
                                continue
        
        # 2. Search by path patterns
        if path_patterns:
            for pattern in path_patterns:
                # Convert relative pattern to absolute
                search_pattern = os.path.join(repo_path, pattern)
                matched_paths = glob.glob(search_pattern, recursive=True)
                
                for file_path in matched_paths:
                    if os.path.isfile(file_path):
                        relative_path = os.path.relpath(file_path, repo_path)
                        file_name = os.path.basename(file_path)
                        
                        if should_skip_file(file_name):
                            continue
                            
                        try:
                            stat = os.stat(file_path)
                            found_files.append({
                                'path': file_path,
                                'relative_path': relative_path,
                                'size': stat.st_size,
                                'match_type': 'path_pattern',
                                'match_pattern': pattern,
                                'language': detect_language(file_name),
                                'modified_time': stat.st_mtime
                            })
                        except (OSError, PermissionError):
                            continue
        
        # 3. Search by content keywords (limited search for performance)
        if content_keywords:
            # First get all text files to search
            text_extensions = {'.py', '.js', '.ts', '.java', '.cs', '.cpp', '.c', '.h', '.hpp', 
                             '.go', '.php', '.rb', '.rs', '.swift', '.kt', '.scala', '.pl', 
                             '.sh', '.bash', '.ps1', '.yaml', '.yml', '.json', '.xml', '.html', 
                             '.css', '.scss', '.sass', '.vue', '.svelte', '.md', '.txt'}
            
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if not should_skip_directory(d)]
                
                for file_name in files:
                    file_ext = Path(file_name).suffix.lower()
                    if file_ext in text_extensions and not should_skip_file(file_name):
                        file_path = os.path.join(root, file_name)
                        relative_path = os.path.relpath(file_path, repo_path)
                        
                        try:
                            # Check file size (skip very large files for content search)
                            stat = os.stat(file_path)
                            if stat.st_size > 1024 * 1024:  # Skip files larger than 1MB
                                continue
                                
                            # Read and search content
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                
                            # Check if any keyword matches
                            matched_keywords = []
                            for keyword in content_keywords:
                                if re.search(keyword, content, re.IGNORECASE):
                                    matched_keywords.append(keyword)
                            
                            if matched_keywords:
                                found_files.append({
                                    'path': file_path,
                                    'relative_path': relative_path,
                                    'size': stat.st_size,
                                    'match_type': 'content_keyword',
                                    'match_pattern': ', '.join(matched_keywords),
                                    'language': detect_language(file_name),
                                    'modified_time': stat.st_mtime
                                })
                        except (OSError, PermissionError, UnicodeDecodeError):
                            continue
        
        # Remove duplicates (same file matched by multiple patterns)
        unique_files = {}
        for file_info in found_files:
            path = file_info['relative_path']
            if path not in unique_files:
                unique_files[path] = file_info
            else:
                # Combine match information
                existing = unique_files[path]
                existing['match_pattern'] += f" + {file_info['match_pattern']}"
                existing['match_type'] += f" + {file_info['match_type']}"
        
        found_files = list(unique_files.values())
        
        # Sort by size (largest first) and limit results
        found_files.sort(key=lambda x: x['size'], reverse=True)
        if len(found_files) > max_files:
            found_files = found_files[:max_files]
        
        # Generate output
        total_size = sum(f['size'] for f in found_files)
        
        output = f"""# 🔍 Smart File Pattern Search Results
        
## 📊 Search Summary
- **Repository**: `{repo_path}`
- **Files Found**: {len(found_files)}
- **Total Size**: {total_size / (1024*1024):.1f} MB ({total_size:,} bytes)
- **Search Patterns**:
"""
        
        if filename_patterns:
            output += f"  - **Filename patterns**: {filename_patterns}\n"
        if path_patterns:
            output += f"  - **Path patterns**: {path_patterns}\n"
        if content_keywords:
            output += f"  - **Content keywords**: {content_keywords}\n"
        
        # Group by match type
        by_match_type = {}
        for file_info in found_files:
            match_type = file_info['match_type'].split(' + ')[0]  # Get primary match type
            if match_type not in by_match_type:
                by_match_type[match_type] = []
            by_match_type[match_type].append(file_info)
        
        for match_type, files in by_match_type.items():
            output += f"\n## 📁 Files found by {match_type.replace('_', ' ').title()}\n"
            output += f"Found {len(files)} files:\n\n"
            
            for i, file_info in enumerate(files, 1):
                size_mb = file_info['size'] / (1024*1024)
                output += f"{i:3d}. `{file_info['relative_path']}` "
                output += f"({size_mb:.2f} MB, {file_info['language']}) - Matched: {file_info['match_pattern']}\n"
        
        output += f"""
        
## 💡 Usage with Analysis Tools
To analyze these files, use:
- `read_file_smart_shared(file_path, repo_path="{repo_path}")` for content analysis
- `list_all_code_files_shared("{repo_path}", extensions=[...])` for comprehensive scanning
        """
        
        return output
        
    except Exception as e:
        return f"❌ Error in smart file pattern search: {str(e)}"


@function_tool
async def find_code_references_shared(
    repo_path: str,
    symbol: str,
    symbol_type: str = "auto",
    file_extensions: Optional[List[str]] = None,
    max_results: int = 500
) -> str:
    """
    Find all references to a specific code symbol (function, class, variable, etc.) across the repository.
    Similar to IDE's "Find References" functionality.
    
    Args:
        repo_path: Path to the repository root
        symbol: The symbol to search for (e.g., "getUserById", "UserService", "DATABASE_URL")
        symbol_type: Type of symbol ("function", "class", "variable", "auto" for automatic detection)
        file_extensions: List of file extensions to search in (default: all code files)
        max_results: Maximum number of references to return (default: 500)
    
    Returns:
        Formatted string with all found references and their contexts
    """
    try:
        import ast
        
        # Check if this looks like a GitHub repo name and adjust path
        if not os.path.exists(repo_path):
            potential_repo_path = os.path.join("repos", repo_path)
            if os.path.exists(potential_repo_path):
                repo_path = potential_repo_path
            else:
                return f"❌ Error: Repository path does not exist: {repo_path} (also tried repos/{repo_path})"
        
        repo_path = os.path.abspath(repo_path)
        references = []
        definitions = []
        
        # Default file extensions for code analysis
        if file_extensions is None:
            file_extensions = ['.py', '.js', '.ts', '.java', '.cs', '.cpp', '.c', '.h', '.hpp', 
                             '.go', '.php', '.rb', '.rs', '.swift', '.kt', '.scala']
        
        # Normalize extensions
        file_extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in file_extensions]
        
        # Different search patterns based on symbol type
        search_patterns = []
        
        if symbol_type in ["function", "auto"]:
            # Function call patterns
            search_patterns.extend([
                rf'\b{re.escape(symbol)}\s*\(',  # function()
                rf'\.{re.escape(symbol)}\s*\(',  # obj.function()
                rf'->{re.escape(symbol)}\s*\(',  # ptr->function() (C/C++)
                rf'::{re.escape(symbol)}\s*\(',  # namespace::function() (C++)
            ])
        
        if symbol_type in ["class", "auto"]:
            # Class usage patterns
            search_patterns.extend([
                rf'\b{re.escape(symbol)}\b',  # Simple class name
                rf'new\s+{re.escape(symbol)}\s*\(',  # new ClassName()
                rf'instanceof\s+{re.escape(symbol)}\b',  # instanceof ClassName
                rf'extends\s+{re.escape(symbol)}\b',  # extends ClassName
                rf'implements\s+{re.escape(symbol)}\b',  # implements ClassName
                rf':\s*{re.escape(symbol)}\b',  # Type annotation
            ])
        
        if symbol_type in ["variable", "auto"]:
            # Variable usage patterns
            search_patterns.extend([
                rf'\b{re.escape(symbol)}\b',  # Simple variable name
                rf'\.{re.escape(symbol)}\b',  # obj.variable
                rf'->{re.escape(symbol)}\b',  # ptr->variable
            ])
        
        # If auto detection, include all patterns
        if symbol_type == "auto":
            search_patterns = list(set(search_patterns))  # Remove duplicates
        
        # Search through files
        for root, dirs, files in os.walk(repo_path):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if not should_skip_directory(d)]
            
            for file_name in files:
                file_ext = Path(file_name).suffix.lower()
                if file_ext not in file_extensions or should_skip_file(file_name):
                    continue
                
                file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(file_path, repo_path)
                
                try:
                    # Check file size (skip very large files)
                    stat = os.stat(file_path)
                    if stat.st_size > 2 * 1024 * 1024:  # Skip files larger than 2MB
                        continue
                    
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    lines = content.split('\n')
                    
                    # Search for patterns in each line
                    for line_num, line in enumerate(lines, 1):
                        line_stripped = line.strip()
                        if not line_stripped or line_stripped.startswith(('#', '//', '/*', '*')):
                            continue  # Skip comments and empty lines
                        
                        for pattern in search_patterns:
                            matches = re.finditer(pattern, line, re.IGNORECASE)
                            for match in matches:
                                # Determine if this is likely a definition or reference
                                is_definition = _is_likely_definition(line, symbol, file_ext)
                                
                                reference_info = {
                                    'file_path': file_path,
                                    'relative_path': relative_path,
                                    'line_number': line_num,
                                    'line_content': line.strip(),
                                    'match_start': match.start(),
                                    'match_end': match.end(),
                                    'pattern_matched': pattern,
                                    'language': detect_language(file_name),
                                    'is_definition': is_definition,
                                    'context_before': lines[max(0, line_num-2):line_num-1] if line_num > 1 else [],
                                    'context_after': lines[line_num:line_num+2] if line_num < len(lines) else []
                                }
                                
                                if is_definition:
                                    definitions.append(reference_info)
                                else:
                                    references.append(reference_info)
                                
                                # Limit results to prevent memory issues
                                if len(references) + len(definitions) >= max_results:
                                    break
                            
                            if len(references) + len(definitions) >= max_results:
                                break
                        
                        if len(references) + len(definitions) >= max_results:
                            break
                    
                except (OSError, PermissionError, UnicodeDecodeError):
                    continue
                
                if len(references) + len(definitions) >= max_results:
                    break
        
        # Sort results
        definitions.sort(key=lambda x: (x['relative_path'], x['line_number']))
        references.sort(key=lambda x: (x['relative_path'], x['line_number']))
        
        # Generate output
        total_found = len(definitions) + len(references)
        
        output = f"""# 🔍 Code References for '{symbol}'

## 📊 Search Summary
- **Repository**: `{repo_path}`
- **Symbol**: `{symbol}`
- **Symbol Type**: {symbol_type}
- **Total References**: {total_found} (Definitions: {len(definitions)}, References: {len(references)})
- **File Extensions Searched**: {file_extensions}

"""
        
        # Show definitions first
        if definitions:
            output += f"## 🎯 Definitions ({len(definitions)})\n\n"
            for i, ref in enumerate(definitions, 1):
                output += f"### {i}. `{ref['relative_path']}:{ref['line_number']}`\n"
                output += f"**Language**: {ref['language']}\n"
                output += f"```{ref['language'].lower()}\n{ref['line_content']}\n```\n\n"
        
        # Show references
        if references:
            output += f"## 📍 References ({len(references)})\n\n"
            
            # Group by file for better organization
            by_file = {}
            for ref in references:
                file_path = ref['relative_path']
                if file_path not in by_file:
                    by_file[file_path] = []
                by_file[file_path].append(ref)
            
            for file_path, file_refs in by_file.items():
                output += f"### 📄 {file_path} ({len(file_refs)} references)\n"
                output += f"**Language**: {file_refs[0]['language']}\n\n"
                
                for ref in file_refs:
                    output += f"**Line {ref['line_number']}**:\n"
                    output += f"```{ref['language'].lower()}\n{ref['line_content']}\n```\n\n"
        
        if not definitions and not references:
            output += f"❌ **No references found** for symbol '{symbol}' in the repository.\n\n"
            output += "**Suggestions**:\n"
            output += f"- Check if the symbol name is spelled correctly\n"
            output += f"- Try different symbol_type: 'function', 'class', 'variable', or 'auto'\n"
            output += f"- Verify the file extensions cover the languages you're interested in\n"
        
        output += f"""
## 💡 Usage Tips
- **Read specific file**: `read_file_smart_shared("{definitions[0]['relative_path'] if definitions else references[0]['relative_path'] if references else 'path'}", repo_path="{repo_path}")`
- **Search related symbols**: Use `find_code_references_shared()` with related function/class names
- **Analyze file context**: Use `get_file_context_shared()` for broader understanding
"""
        
        return output
        
    except Exception as e:
        return f"❌ Error in code reference search: {str(e)}"


def _is_likely_definition(line: str, symbol: str, file_ext: str) -> bool:
    """
    Heuristic to determine if a line contains a definition rather than a reference.
    """
    line_lower = line.lower().strip()
    symbol_lower = symbol.lower()
    
    # Common definition keywords by language
    definition_keywords = {
        '.py': ['def ', 'class ', 'async def '],
        '.js': ['function ', 'const ', 'let ', 'var ', 'class '],
        '.ts': ['function ', 'const ', 'let ', 'var ', 'class ', 'interface ', 'type '],
        '.java': ['public ', 'private ', 'protected ', 'class ', 'interface ', 'enum '],
        '.cs': ['public ', 'private ', 'protected ', 'class ', 'interface ', 'struct ', 'enum '],
        '.cpp': ['class ', 'struct ', 'enum ', 'namespace '],
        '.c': ['struct ', 'enum ', 'typedef '],
        '.go': ['func ', 'type ', 'var ', 'const '],
        '.php': ['function ', 'class ', 'interface ', 'trait '],
        '.rb': ['def ', 'class ', 'module '],
        '.rs': ['fn ', 'struct ', 'enum ', 'trait ', 'impl '],
    }
    
    keywords = definition_keywords.get(file_ext, [])
    
    # Check if line starts with definition keywords
    for keyword in keywords:
        if keyword in line_lower and symbol_lower in line_lower:
            # Additional check: symbol should appear after the keyword
            keyword_pos = line_lower.find(keyword)
            symbol_pos = line_lower.find(symbol_lower)
            if symbol_pos > keyword_pos:
                return True
    
    # Check for assignment patterns (variable definitions)
    if '=' in line and symbol_lower in line_lower:
        equal_pos = line.find('=')
        symbol_pos = line_lower.find(symbol_lower)
        if symbol_pos < equal_pos:  # Symbol appears before =
            return True
    
    return False