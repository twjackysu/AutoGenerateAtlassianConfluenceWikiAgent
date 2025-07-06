import os
import subprocess
from pathlib import Path
from agents import function_tool


@function_tool
async def clone_github_repo(repo_url: str, local_path: str = None, branch: str = "main") -> str:
    """
    Clone or update a GitHub repository to local filesystem.
    If repository exists, fetch and hard reset to latest.
    If repository doesn't exist, clone fresh.
    
    Args:
        repo_url: GitHub repository URL (e.g., 'https://github.com/user/repo.git' or 'user/repo')
        local_path: Local directory path to clone to (optional, defaults to repo name)
        branch: Branch to clone/update (default: 'main')
    
    Returns:
        Status message about clone/update operation
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
            # Check if it's a git repository
            if os.path.exists(os.path.join(local_path, '.git')):
                # Repository exists, fetch and hard reset
                try:
                    # Fetch latest changes
                    subprocess.run(['git', 'fetch', 'origin'], cwd=local_path, capture_output=True, text=True, check=True)
                    
                    # Hard reset to latest origin/branch
                    subprocess.run(['git', 'reset', '--hard', f'origin/{branch}'], cwd=local_path, capture_output=True, text=True, check=True)
                    
                    # Clean untracked files
                    subprocess.run(['git', 'clean', '-fd'], cwd=local_path, capture_output=True, text=True, check=True)
                    
                    return f"Successfully updated {repo_url} at {local_path} to latest {branch}"
                    
                except subprocess.CalledProcessError as e:
                    # If fetch/reset fails, remove directory and clone fresh
                    subprocess.run(['rm', '-rf', local_path], check=True)
                    cmd = ['git', 'clone', '-b', branch, repo_url, local_path]
                    subprocess.run(cmd, capture_output=True, text=True, check=True)
                    return f"Repository had issues, re-cloned {repo_url} to {local_path}"
            else:
                # Directory exists but not a git repo, remove and clone
                subprocess.run(['rm', '-rf', local_path], check=True)
                cmd = ['git', 'clone', '-b', branch, repo_url, local_path]
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                return f"Directory existed but wasn't a git repo, cloned {repo_url} to {local_path}"
        else:
            # Directory doesn't exist, clone fresh
            cmd = ['git', 'clone', '-b', branch, repo_url, local_path]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return f"Successfully cloned {repo_url} to {local_path}"
        
    except subprocess.CalledProcessError as e:
        return f"Error cloning repository: {e.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"