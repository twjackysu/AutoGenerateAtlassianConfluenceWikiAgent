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