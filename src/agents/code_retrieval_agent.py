"""
Code Retrieval Agent - Responsible for fetching and reading code repositories
"""
import os
import asyncio
from typing import List, Dict, Optional, Any
from pathlib import Path
import git
from git import Repo
import aiofiles
from agents import Agent, Tool
from src.models.claude_model import ClaudeModel
from src.config import config

class CodeRetrievalAgent:
    """Agent responsible for code retrieval operations"""
    
    def __init__(self):
        self.agent = Agent(
            name="Code Retrieval Agent",
            instructions="""
            You are a code retrieval specialist. Your responsibilities include:
            1. Cloning or accessing repositories from GitHub or local storage
            2. Reading and indexing all relevant code files
            3. Filtering files based on supported extensions
            4. Preparing file contents for analysis
            5. Providing structured file information to other agents
            
            Be thorough in your file discovery and ensure you capture all relevant code files.
            Respect file size limits and skip binary or excessively large files.
            """,
            model=ClaudeModel(),
            tools=[
                Tool(
                    name="clone_repository",
                    description="Clone a Git repository from a URL",
                    function=self.clone_repository
                ),
                Tool(
                    name="read_local_directory",
                    description="Read files from a local directory",
                    function=self.read_local_directory
                ),
                Tool(
                    name="get_file_content",
                    description="Get the content of a specific file",
                    function=self.get_file_content
                ),
                Tool(
                    name="list_code_files",
                    description="List all code files in a directory",
                    function=self.list_code_files
                )
            ]
        )
    
    async def clone_repository(self, repo_url: str, local_path: str = None) -> Dict[str, Any]:
        """Clone a Git repository to local storage"""
        try:
            if not local_path:
                repo_name = repo_url.split('/')[-1].replace('.git', '')
                local_path = f"./temp_repos/{repo_name}"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Clone the repository
            repo = Repo.clone_from(repo_url, local_path)
            
            return {
                "status": "success",
                "message": f"Repository cloned successfully to {local_path}",
                "local_path": local_path,
                "repo_info": {
                    "url": repo_url,
                    "branch": repo.active_branch.name,
                    "commit": repo.head.commit.hexsha,
                    "last_modified": repo.head.commit.committed_datetime.isoformat()
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to clone repository: {str(e)}"
            }
    
    async def read_local_directory(self, directory_path: str) -> Dict[str, Any]:
        """Read and index files from a local directory"""
        try:
            path = Path(directory_path)
            if not path.exists():
                return {
                    "status": "error",
                    "message": f"Directory {directory_path} does not exist"
                }
            
            files_info = await self.list_code_files(directory_path)
            
            return {
                "status": "success",
                "message": f"Successfully indexed {len(files_info['files'])} files",
                "directory_path": directory_path,
                "files": files_info['files']
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to read directory: {str(e)}"
            }
    
    async def get_file_content(self, file_path: str) -> Dict[str, Any]:
        """Get the content of a specific file"""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {
                    "status": "error",
                    "message": f"File {file_path} does not exist"
                }
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > config.max_file_size:
                return {
                    "status": "error",
                    "message": f"File {file_path} is too large ({file_size} bytes)"
                }
            
            # Read file content
            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = await file.read()
            
            return {
                "status": "success",
                "file_path": file_path,
                "content": content,
                "size": file_size,
                "extension": path.suffix,
                "name": path.name
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to read file: {str(e)}"
            }
    
    async def list_code_files(self, directory_path: str) -> Dict[str, Any]:
        """List all code files in a directory recursively"""
        try:
            path = Path(directory_path)
            files = []
            
            def should_include_file(file_path: Path) -> bool:
                # Skip hidden files and directories
                if any(part.startswith('.') for part in file_path.parts):
                    return False
                
                # Skip common non-code directories
                skip_dirs = {
                    'node_modules', '__pycache__', '.git', 'venv', 'env',
                    'build', 'dist', 'target', 'bin', 'obj', '.next',
                    'coverage', '.pytest_cache', '.mypy_cache'
                }
                
                if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                    return False
                
                # Check file extension
                return file_path.suffix.lower() in config.supported_extensions
            
            # Walk through directory
            for file_path in path.rglob('*'):
                if file_path.is_file() and should_include_file(file_path):
                    try:
                        stat = file_path.stat()
                        if stat.st_size <= config.max_file_size:
                            files.append({
                                "path": str(file_path),
                                "relative_path": str(file_path.relative_to(path)),
                                "name": file_path.name,
                                "extension": file_path.suffix,
                                "size": stat.st_size,
                                "modified": stat.st_mtime
                            })
                    except (OSError, ValueError):
                        # Skip files that can't be accessed
                        continue
            
            return {
                "status": "success",
                "directory": directory_path,
                "total_files": len(files),
                "files": files
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to list files: {str(e)}"
            }
