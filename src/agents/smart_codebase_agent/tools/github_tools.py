import os
import subprocess
from pathlib import Path
from agents import function_tool


@function_tool
async def clone_github_repo(repo_url: str, local_path: str = None, branch: str = "main") -> str:
    """
    Clone a GitHub repository to local filesystem.
    
    Args:
        repo_url: GitHub repository URL (e.g., 'https://github.com/user/repo.git' or 'user/repo')
        local_path: Local directory path to clone to (optional, defaults to repo name)
        branch: Branch to clone (default: 'main')
    
    Returns:
        Path to the cloned repository
    """
    try:
        if not repo_url.startswith('http'):
            if '/' in repo_url:
                repo_url = f"https://github.com/{repo_url}.git"
            else:
                return f"Invalid repo format: {repo_url}. Use 'user/repo' or full URL."
        
        if local_path is None:
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            local_path = f"./repos/{repo_name}"
        
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        
        if os.path.exists(local_path):
            subprocess.run(['rm', '-rf', local_path], check=True)
        
        cmd = ['git', 'clone', '-b', branch, repo_url, local_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        return f"Successfully cloned {repo_url} to {local_path}"
        
    except subprocess.CalledProcessError as e:
        return f"Error cloning repository: {e.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"