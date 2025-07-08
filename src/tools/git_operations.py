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
    Clone a GitHub repository to local filesystem.
    If repository exists, remove it and clone fresh.
    If repository doesn't exist, clone fresh.
    
    Args:
        repo_url: GitHub repository URL (e.g., 'https://github.com/user/repo.git' or 'user/repo')
        local_path: Local directory path to clone to (optional, defaults to repo name)
        branch: Branch to clone (optional, uses repository's default branch if not specified)
    
    Returns:
        Status message about clone operation
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
            # Repository exists, remove it and clone fresh
            removal_success = False
            last_error = None
            
            # Method 1: Try normal shutil.rmtree
            try:
                shutil.rmtree(local_path, ignore_errors=False)
                removal_success = not os.path.exists(local_path)
                if removal_success:
                    pass  # Success, no need to try other methods
            except Exception as e:
                last_error = f"Method 1 failed: {e}"
            
            # Method 2: If normal removal fails, try force removal
            if not removal_success:
                try:
                    if os.name == 'nt':  # Windows
                        result = subprocess.run(['rmdir', '/s', '/q', local_path], 
                                              shell=True, capture_output=True, text=True)
                    else:  # Unix/Linux/macOS
                        result = subprocess.run(['rm', '-rf', local_path], 
                                              capture_output=True, text=True)
                    removal_success = not os.path.exists(local_path)
                    if not removal_success:
                        last_error = f"Method 2 failed: {result.stderr if result.stderr else 'Unknown error'}"
                except Exception as e:
                    last_error = f"Method 2 exception: {e}"
            
            # Method 3: Python-based recursive removal with attribute changes
            if not removal_success:
                try:
                    import stat
                    def remove_readonly(func, path, exc):
                        try:
                            os.chmod(path, stat.S_IWRITE)
                            func(path)
                        except:
                            pass
                    
                    shutil.rmtree(local_path, onerror=remove_readonly)
                    removal_success = not os.path.exists(local_path)
                    if not removal_success:
                        last_error = "Method 3 failed: Readonly removal unsuccessful"
                except Exception as e:
                    last_error = f"Method 3 exception: {e}"
            
            # Final check - if directory still exists, create a more informative error
            if not removal_success and os.path.exists(local_path):
                # Get directory info for debugging
                try:
                    import stat
                    stat_info = os.stat(local_path)
                    permissions = oct(stat_info.st_mode)[-3:]
                    size_info = f", size: {stat_info.st_size} bytes" if os.path.isfile(local_path) else ""
                    debug_info = f" (permissions: {permissions}{size_info})"
                except:
                    debug_info = ""
                
                return f"❌ Error: Unable to remove existing directory {local_path}{debug_info}. Last error: {last_error}. Please remove it manually and try again."
            
            # Clone fresh repository
            if branch:
                # Try cloning with specified branch first
                try:
                    cmd = ['git', 'clone', '-b', branch, repo_url, local_path]
                    subprocess.run(cmd, capture_output=True, text=True, check=True)
                    return f"Successfully removed existing repo and cloned {repo_url} to {local_path} on branch {branch}"
                except subprocess.CalledProcessError:
                    # If branch doesn't exist, fall back to default branch
                    pass
            
            # Clone without specifying branch (uses repository's default branch)
            cmd = ['git', 'clone', repo_url, local_path]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return f"Successfully removed existing repo and cloned {repo_url} to {local_path}"
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