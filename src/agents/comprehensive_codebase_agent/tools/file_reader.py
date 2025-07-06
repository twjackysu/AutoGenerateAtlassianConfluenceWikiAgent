import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass
from agents import function_tool


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


def estimate_tokens(text: str) -> int:
    """Estimate token count for text content"""
    # More accurate estimation based on actual text content
    # Rough estimation: 1 token ≈ 3.5-4 characters, accounting for whitespace
    return len(text) // 4


def detect_language_from_path(file_path: str) -> str:
    """Detect programming language from file extension"""
    ext = Path(file_path).suffix.lower()
    language_map = {
        '.py': 'python',
        '.cpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp',
        '.c': 'c', '.h': 'c',
        '.hpp': 'cpp',
        '.java': 'java',
        '.cs': 'csharp',
        '.js': 'javascript', '.jsx': 'javascript',
        '.ts': 'typescript', '.tsx': 'typescript',
        '.sql': 'sql',
        '.go': 'go',
        '.php': 'php',
        '.rb': 'ruby',
        '.rs': 'rust',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala'
    }
    return language_map.get(ext, 'text')


def smart_chunk_by_functions(content: str, language: str, max_tokens: int = 2000) -> List[Tuple[str, str]]:
    """
    Intelligently chunk content by functions/methods/classes based on language.
    Returns list of (chunk_content, chunk_type) tuples.
    """
    chunks = []
    
    if language == 'python':
        chunks = _chunk_python_code(content, max_tokens)
    elif language in ['javascript', 'typescript']:
        chunks = _chunk_javascript_code(content, max_tokens)
    elif language == 'java':
        chunks = _chunk_java_code(content, max_tokens)
    elif language == 'csharp':
        chunks = _chunk_csharp_code(content, max_tokens)
    elif language in ['cpp', 'c']:
        chunks = _chunk_c_cpp_code(content, max_tokens)
    else:
        # Fallback to simple line-based chunking
        chunks = _chunk_by_lines(content, max_tokens)
    
    return chunks if chunks else [("", "empty")]


def _chunk_python_code(content: str, max_tokens: int) -> List[Tuple[str, str]]:
    """Chunk Python code by classes and functions"""
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_type = "code_block"
    bracket_depth = 0
    in_function_or_class = False
    
    for line in lines:
        stripped = line.strip()
        
        # Detect class or function definition
        if stripped.startswith(('def ', 'class ', 'async def ')):
            # If we have accumulated content, save it as a chunk
            if current_chunk:
                chunk_content = '\n'.join(current_chunk)
                if estimate_tokens(chunk_content) > 50:  # Only save non-trivial chunks
                    chunks.append((chunk_content, current_type))
                current_chunk = []
            
            current_type = "function" if stripped.startswith(('def ', 'async def ')) else "class"
            in_function_or_class = True
            current_chunk.append(line)
        
        elif in_function_or_class:
            current_chunk.append(line)
            
            # Count indentation to determine when function/class ends
            if stripped and not line.startswith((' ', '\t')):
                # Back to top level - function/class ended
                chunk_content = '\n'.join(current_chunk[:-1])  # Exclude the current line
                if estimate_tokens(chunk_content) > 50:
                    chunks.append((chunk_content, current_type))
                
                current_chunk = [line]
                current_type = "code_block"
                in_function_or_class = False
        
        else:
            current_chunk.append(line)
            
            # Check if current chunk is getting too large
            if len(current_chunk) > 50:  # Arbitrary line limit
                chunk_content = '\n'.join(current_chunk)
                if estimate_tokens(chunk_content) > max_tokens:
                    chunks.append((chunk_content, current_type))
                    current_chunk = []
    
    # Add remaining content
    if current_chunk:
        chunk_content = '\n'.join(current_chunk)
        if estimate_tokens(chunk_content) > 50:
            chunks.append((chunk_content, current_type))
    
    return chunks


def _chunk_javascript_code(content: str, max_tokens: int) -> List[Tuple[str, str]]:
    """Chunk JavaScript/TypeScript code by functions and classes"""
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_type = "code_block"
    brace_depth = 0
    in_function = False
    
    for line in lines:
        stripped = line.strip()
        
        # Detect function/class definitions
        if any(pattern in stripped for pattern in [
            'function ', 'class ', '=>', 'const ', 'let ', 'var '
        ]) and ('{' in stripped or '=>' in stripped):
            
            if current_chunk and brace_depth == 0:
                chunk_content = '\n'.join(current_chunk)
                if estimate_tokens(chunk_content) > 50:
                    chunks.append((chunk_content, current_type))
                current_chunk = []
            
            current_type = "function" if 'function' in stripped or '=>' in stripped else "code_block"
            if 'class' in stripped:
                current_type = "class"
        
        current_chunk.append(line)
        
        # Count braces to track scope
        brace_depth += line.count('{') - line.count('}')
        
        # If we're back to top level and have substantial content
        if brace_depth == 0 and len(current_chunk) > 10:
            chunk_content = '\n'.join(current_chunk)
            if estimate_tokens(chunk_content) > max_tokens:
                chunks.append((chunk_content, current_type))
                current_chunk = []
                current_type = "code_block"
    
    # Add remaining content
    if current_chunk:
        chunk_content = '\n'.join(current_chunk)
        if estimate_tokens(chunk_content) > 50:
            chunks.append((chunk_content, current_type))
    
    return chunks


def _chunk_java_code(content: str, max_tokens: int) -> List[Tuple[str, str]]:
    """Chunk Java code by classes and methods"""
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_type = "code_block"
    brace_depth = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Detect class or method definitions
        if any(keyword in stripped for keyword in ['public class', 'private class', 'class ']):
            current_type = "class"
        elif any(keyword in stripped for keyword in ['public ', 'private ', 'protected ']) and '(' in stripped:
            current_type = "method"
        
        current_chunk.append(line)
        brace_depth += line.count('{') - line.count('}')
        
        # Check for chunk completion
        if brace_depth == 0 and len(current_chunk) > 5:
            chunk_content = '\n'.join(current_chunk)
            if estimate_tokens(chunk_content) > max_tokens:
                chunks.append((chunk_content, current_type))
                current_chunk = []
                current_type = "code_block"
    
    if current_chunk:
        chunk_content = '\n'.join(current_chunk)
        if estimate_tokens(chunk_content) > 50:
            chunks.append((chunk_content, current_type))
    
    return chunks


def _chunk_csharp_code(content: str, max_tokens: int) -> List[Tuple[str, str]]:
    """Chunk C# code by classes and methods"""
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_type = "code_block"
    brace_depth = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Detect class, method, or property definitions
        if 'class ' in stripped and '{' in line:
            current_type = "class"
        elif any(keyword in stripped for keyword in ['public ', 'private ', 'internal ', 'protected ']) and '(' in stripped:
            current_type = "method"
        elif 'namespace ' in stripped:
            current_type = "namespace"
        
        current_chunk.append(line)
        brace_depth += line.count('{') - line.count('}')
        
        if brace_depth == 0 and len(current_chunk) > 5:
            chunk_content = '\n'.join(current_chunk)
            if estimate_tokens(chunk_content) > max_tokens:
                chunks.append((chunk_content, current_type))
                current_chunk = []
                current_type = "code_block"
    
    if current_chunk:
        chunk_content = '\n'.join(current_chunk)
        if estimate_tokens(chunk_content) > 50:
            chunks.append((chunk_content, current_type))
    
    return chunks


def _chunk_c_cpp_code(content: str, max_tokens: int) -> List[Tuple[str, str]]:
    """Chunk C/C++ code by functions and classes"""
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_type = "code_block"
    brace_depth = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Simple detection for functions (lines ending with { after a })
        if stripped.endswith('{') and '(' in stripped:
            current_type = "function"
        elif 'class ' in stripped or 'struct ' in stripped:
            current_type = "class"
        
        current_chunk.append(line)
        brace_depth += line.count('{') - line.count('}')
        
        if brace_depth == 0 and len(current_chunk) > 5:
            chunk_content = '\n'.join(current_chunk)
            if estimate_tokens(chunk_content) > max_tokens:
                chunks.append((chunk_content, current_type))
                current_chunk = []
                current_type = "code_block"
    
    if current_chunk:
        chunk_content = '\n'.join(current_chunk)
        if estimate_tokens(chunk_content) > 50:
            chunks.append((chunk_content, current_type))
    
    return chunks


def _chunk_by_lines(content: str, max_tokens: int) -> List[Tuple[str, str]]:
    """Fallback chunking by lines when language-specific chunking isn't available"""
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    
    for line in lines:
        current_chunk.append(line)
        
        # Check if chunk is getting too large
        chunk_content = '\n'.join(current_chunk)
        if estimate_tokens(chunk_content) >= max_tokens:
            chunks.append((chunk_content, "code_block"))
            current_chunk = []
    
    # Add remaining lines
    if current_chunk:
        chunk_content = '\n'.join(current_chunk)
        chunks.append((chunk_content, "code_block"))
    
    return chunks


@function_tool
async def read_file_smart(
    file_path: str,
    chunk_size: Union[str, int] = "auto",
    chunk_index: Optional[int] = None,
    max_tokens_per_chunk: int = 2000
) -> str:
    """
    Intelligently read a file with smart chunking strategies.
    
    Args:
        file_path: Path to the file to read
        chunk_size: Either "auto" for intelligent chunking, or an integer for fixed-size chunks
        chunk_index: If specified, return only this chunk (0-based). If None, return all chunks
        max_tokens_per_chunk: Maximum tokens per chunk when using auto chunking
    
    Returns:
        Formatted string with file content and metadata
    """
    try:
        if not os.path.exists(file_path):
            return f"❌ Error: File does not exist: {file_path}"
        
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
        language = detect_language_from_path(file_path)
        total_lines = len(content.split('\n'))
        
        # Create chunks
        chunks = []
        
        if chunk_size == "auto":
            # Smart chunking based on language
            raw_chunks = smart_chunk_by_functions(content, language, max_tokens_per_chunk)
            
            for i, (chunk_content, chunk_type) in enumerate(raw_chunks):
                if chunk_content.strip():  # Skip empty chunks
                    chunk_lines = chunk_content.split('\n')
                    start_line = 1 if i == 0 else sum(len(c[0].split('\n')) for c in raw_chunks[:i]) + 1
                    end_line = start_line + len(chunk_lines) - 1
                    
                    chunk = FileChunk(
                        content=chunk_content,
                        chunk_index=i,
                        total_chunks=len(raw_chunks),
                        start_line=start_line,
                        end_line=end_line,
                        estimated_tokens=estimate_tokens(chunk_content),
                        chunk_type=chunk_type
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
        
        # Return all chunks
        return _format_full_file_output(result)
        
    except Exception as e:
        return f"❌ Error reading file {file_path}: {str(e)}"


def _format_single_chunk_output(result: ReadResult, chunk: FileChunk) -> str:
    """Format output for a single chunk"""
    output = f"""# 📄 File Chunk: {os.path.basename(result.file_path)}

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
    """Format output for complete file overview (without full content to prevent large API calls)"""
    relative_path = os.path.basename(result.file_path)
    
    output = f"""# 📄 File Analysis Overview: {relative_path}

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
To read the actual content, use `read_file_smart()` with specific chunk indices:

"""
    
    for i, chunk in enumerate(result.chunks):
        output += f"- **Chunk {i}**: `read_file_smart(\"{result.file_path}\", chunk_index={i})` - {chunk.chunk_type} ({chunk.estimated_tokens:,} tokens)\n"
    
    output += f"""

## 📝 Content Preview (First Chunk Only)
"""
    
    # Only include first chunk to provide context without overwhelming tokens
    if result.chunks:
        first_chunk = result.chunks[0]
        # Limit preview to first 20 lines to keep token count low
        preview_lines = first_chunk.content.split('\n')[:20]
        preview_content = '\n'.join(preview_lines)
        if len(first_chunk.content.split('\n')) > 20:
            preview_content += f"\n... ({len(first_chunk.content.split('\n')) - 20} more lines in this chunk)"
        
        output += f"""
**Preview of Chunk 1** ({first_chunk.chunk_type}):

```{result.language}
{preview_content}
```

⚠️ **Note**: This is only a preview. Use `read_file_smart()` with `chunk_index` parameter to read specific chunks without exceeding token limits.
"""
    
    return output