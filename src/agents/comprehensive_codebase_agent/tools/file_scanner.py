import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Set
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


# Supported file extensions and their languages
LANGUAGE_EXTENSIONS = {
    '.py': 'Python',
    '.cpp': 'C++',
    '.cc': 'C++',
    '.cxx': 'C++',
    '.c': 'C',
    '.h': 'C/C++',
    '.hpp': 'C++',
    '.java': 'Java',
    '.cs': 'C#',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.jsx': 'JavaScript',
    '.tsx': 'TypeScript',
    '.sql': 'SQL',
    '.go': 'Go',
    '.php': 'PHP',
    '.rb': 'Ruby',
    '.rs': 'Rust',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
    '.pl': 'Perl',
    '.sh': 'Shell',
    '.bash': 'Shell',
    '.ps1': 'PowerShell',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.json': 'JSON',
    '.xml': 'XML',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.sass': 'SASS',
    '.vue': 'Vue',
    '.svelte': 'Svelte'
}

# Directories to skip
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

# Files to skip
SKIP_FILES = {
    '.gitignore', '.gitattributes',
    '.dockerignore', 'Dockerfile',
    'package-lock.json', 'yarn.lock',
    'pipfile.lock', 'poetry.lock',
    'composer.lock', 'gemfile.lock',
    '.env', '.env.local', '.env.example',
    'readme.md', 'license', 'changelog.md'
}


def estimate_tokens(content_size: int) -> int:
    """Estimate token count based on file size (rough approximation)"""
    # Rough estimation: 1 token ≈ 4 characters
    return content_size // 4


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
async def list_all_code_files(
    repo_path: str,
    extensions: Optional[List[str]] = None,
    include_config: bool = True,
    max_file_size: int = 10 * 1024 * 1024  # 10MB default limit
) -> str:
    """
    Recursively list all code files in a repository with metadata.
    
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
        if not os.path.exists(repo_path):
            return f"❌ Error: Repository path does not exist: {repo_path}"
        
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


def _scan_repository(
    repo_path: str,
    extensions: Optional[List[str]] = None,
    include_config: bool = True,
    max_file_size: int = 10 * 1024 * 1024  # 10MB default limit
) -> List[FileInfo]:
    """
    Internal function to scan repository and return FileInfo objects.
    This is the core logic extracted from list_all_code_files for internal use.
    """
    if not os.path.exists(repo_path):
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
    
    repo_path = os.path.abspath(repo_path)
    files: List[FileInfo] = []
    
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
                
            except (OSError, PermissionError):
                continue
    
    # Sort files by size (largest first) for better batch planning
    files.sort(key=lambda x: x.size, reverse=True)
    
    return files


def _format_file_listing_output(result: Dict) -> str:
    """Format the file listing result as markdown"""
    summary = result['summary']
    files = result['files']
    
    output = f"""# 📁 Code Repository Analysis

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
    for i, file_info in enumerate(files, 1):
        output += f"{i:3d}. `{file_info['relative_path']}` "
        output += f"({file_info['size_mb']:.2f} MB, {file_info['estimated_tokens']:,} tokens, {file_info['language']})\n"
    
    return output