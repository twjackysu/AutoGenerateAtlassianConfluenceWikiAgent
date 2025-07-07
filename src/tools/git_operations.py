"""
Git operations tools - shared version for multi-agent system.
Based on the original github_tools.py but adapted for multi-agent usage.
"""

import os
import subprocess
import shutil
from pathlib import Path
from agents import function_tool


@function_tool
async def clone_github_repo_shared(repo_url: str, local_path: str = None, branch: str = None) -> str:
    """
    Clone or update a GitHub repository to local filesystem.
    If repository exists, fetch and hard reset to latest.
    If repository doesn't exist, clone fresh.
    
    Args:
        repo_url: GitHub repository URL (e.g., 'https://github.com/user/repo.git' or 'user/repo')
        local_path: Local directory path to clone to (optional, defaults to repo name)
        branch: Branch to clone/update (optional, auto-detects default branch if not specified)
    
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
                    
                    # If branch not specified, get default branch
                    if branch is None:
                        result = subprocess.run(['git', 'symbolic-ref', 'refs/remotes/origin/HEAD'], 
                                              cwd=local_path, capture_output=True, text=True)
                        if result.returncode == 0:
                            branch = result.stdout.strip().split('/')[-1]
                        else:
                            # Fallback: try common branch names
                            for fallback_branch in ['main', 'master']:
                                result = subprocess.run(['git', 'show-ref', '--verify', f'refs/remotes/origin/{fallback_branch}'], 
                                                      cwd=local_path, capture_output=True, text=True)
                                if result.returncode == 0:
                                    branch = fallback_branch
                                    break
                            else:
                                branch = 'main'  # Ultimate fallback
                    
                    # Hard reset to latest origin/branch
                    subprocess.run(['git', 'reset', '--hard', f'origin/{branch}'], cwd=local_path, capture_output=True, text=True, check=True)
                    
                    # Clean untracked files
                    subprocess.run(['git', 'clean', '-fd'], cwd=local_path, capture_output=True, text=True, check=True)
                    
                    return f"Successfully updated {repo_url} at {local_path} to latest {branch}"
                    
                except subprocess.CalledProcessError as e:
                    # If fetch/reset fails, remove directory and clone fresh
                    shutil.rmtree(local_path, ignore_errors=True)
                    # Try cloning without specifying branch first
                    cmd = ['git', 'clone', repo_url, local_path]
                    subprocess.run(cmd, capture_output=True, text=True, check=True)
                    return f"Repository had issues, re-cloned {repo_url} to {local_path}"
            else:
                # Directory exists but not a git repo, remove and clone
                shutil.rmtree(local_path, ignore_errors=True)
                cmd = ['git', 'clone', repo_url, local_path]
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                return f"Directory existed but wasn't a git repo, cloned {repo_url} to {local_path}"
        else:
            # Directory doesn't exist, clone fresh
            if branch:
                # Try cloning with specified branch first
                try:
                    cmd = ['git', 'clone', '-b', branch, repo_url, local_path]
                    subprocess.run(cmd, capture_output=True, text=True, check=True)
                    return f"Successfully cloned {repo_url} to {local_path} on branch {branch}"
                except subprocess.CalledProcessError:
                    # If branch doesn't exist, fall back to default branch
                    pass
            
            # Clone without specifying branch (uses repository's default branch)
            cmd = ['git', 'clone', repo_url, local_path]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return f"Successfully cloned {repo_url} to {local_path}"
        
    except subprocess.CalledProcessError as e:
        return f"Error cloning repository: {e.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"