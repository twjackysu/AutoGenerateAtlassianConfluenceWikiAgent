"""
Git operations tools - shared version for multi-agent system.
Based on the original github_tools.py but adapted for multi-agent usage.
Supports custom Git hosts and SSH protocol.
"""

import os
import subprocess
import shutil
from pathlib import Path
from agents import function_tool
from src.logging_system import get_tool_logger


@function_tool
async def clone_github_repo_shared(repo_url: str, local_path: str = None, branch: str = None) -> str:
    """
    Clone a Git repository to local filesystem with support for custom hosts and SSH.
    If repository exists, remove it and clone fresh.
    If repository doesn't exist, clone fresh.
    
    Args:
        repo_url: Git repository URL formats supported:
                 - Full URL: 'https://git.company.com/user/repo.git'
                 - SSH URL: 'git@git.company.com:user/repo.git'  
                 - Short format: 'user/repo' (uses default host and protocol from ENV)
        local_path: Local directory path to clone to (optional, defaults to repo name)
        branch: Branch to clone (optional, uses repository's default branch if not specified)
    
    Environment Variables:
        GIT_HOST: Default Git host (default: github.com)
        GIT_PROTOCOL: Default protocol, 'https' or 'ssh' (default: https)
    
    Returns:
        Status message about clone operation
    """
    logger = get_tool_logger(__name__)
    logger.tool_start("clone_github_repo_shared", repo_url=repo_url, local_path=local_path, branch=branch)
    try:
        # Get environment settings
        default_host = os.getenv('GIT_HOST', 'github.com')
        default_protocol = os.getenv('GIT_PROTOCOL', 'https').lower()
        ssh_key_path = os.getenv('SSH_KEY_PATH')
        
        logger.info(f"Git configuration - Host: {default_host}, Protocol: {default_protocol}")
        if ssh_key_path:
            logger.info(f"SSH key path configured: {ssh_key_path}")
            # Check if SSH key exists
            if os.path.exists(ssh_key_path):
                logger.info("SSH key file exists")
                # Log file permissions
                import stat
                file_stat = os.stat(ssh_key_path)
                permissions = oct(file_stat.st_mode)[-3:]
                logger.info(f"SSH key permissions: {permissions}")
            else:
                logger.warning(f"SSH key file not found at: {ssh_key_path}")
        else:
            logger.warning("No SSH_KEY_PATH configured in environment")
        
        # Handle different URL formats
        if repo_url.startswith(('http://', 'https://', 'git@')):
            # Full URL provided, use as-is
            final_repo_url = repo_url
            logger.info(f"Using full URL as provided: {final_repo_url}")
        elif '/' in repo_url:
            # Short format: user/repo
            if default_protocol == 'ssh':
                final_repo_url = f"git@{default_host}:{repo_url}.git"
                logger.info(f"Converted to SSH URL: {final_repo_url}")
            else:
                final_repo_url = f"https://{default_host}/{repo_url}.git"
                logger.info(f"Converted to HTTPS URL: {final_repo_url}")
        else:
            return f"Invalid repo format: {repo_url}. Use 'user/repo' or full URL."
        
        repo_url = final_repo_url
        
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
                    logger.info(f"Executing git command: {' '.join(cmd)}")
                    
                    # Set up environment for SSH if needed
                    env = os.environ.copy()
                    if ssh_key_path and repo_url.startswith('git@'):
                        env['GIT_SSH_COMMAND'] = f'ssh -i {ssh_key_path} -o StrictHostKeyChecking=no'
                        logger.info(f"Using SSH command: {env['GIT_SSH_COMMAND']}")
                        # Force print to ensure we see this even if logger is swallowed
                        print(f"🔧 SSH Command: {env['GIT_SSH_COMMAND']}")
                    
                    logger.info(f"Starting git clone with timeout=600s")
                    print(f"🔧 Starting git clone: {' '.join(cmd)}")
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env, timeout=600)
                    if result.stdout:
                        logger.info(f"Git stdout: {result.stdout.strip()}")
                    if result.stderr:
                        logger.info(f"Git stderr: {result.stderr.strip()}")
                    logger.info("Git clone with branch succeeded")
                    return f"Successfully removed existing repo and cloned {repo_url} to {local_path} on branch {branch}"
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Git clone with branch failed: {e.stderr}")
                    # If branch doesn't exist, fall back to default branch
                    pass
            
            # Clone without specifying branch (uses repository's default branch)
            cmd = ['git', 'clone', repo_url, local_path]
            logger.info(f"Executing git command: {' '.join(cmd)}")
            
            # Set up environment for SSH if needed
            env = os.environ.copy()
            if ssh_key_path and repo_url.startswith('git@'):
                env['GIT_SSH_COMMAND'] = f'ssh -i {ssh_key_path} -o StrictHostKeyChecking=no'
                logger.info(f"Using SSH command: {env['GIT_SSH_COMMAND']}")
                # Force print to ensure we see this even if logger is swallowed
                print(f"🔧 SSH Command: {env['GIT_SSH_COMMAND']}")
            
            logger.info(f"Starting git clone with timeout=600s")
            print(f"🔧 Starting git clone: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env, timeout=600)
            if result.stdout:
                logger.info(f"Git stdout: {result.stdout.strip()}")
            if result.stderr:
                logger.info(f"Git stderr: {result.stderr.strip()}")
            logger.info("Git clone succeeded")
            return f"Successfully removed existing repo and cloned {repo_url} to {local_path}"
        else:
            # Directory doesn't exist, clone fresh
            logger.info(f"Directory {local_path} doesn't exist, cloning fresh")
            
            if branch:
                # Try cloning with specified branch first
                try:
                    cmd = ['git', 'clone', '-b', branch, repo_url, local_path]
                    logger.info(f"Executing git command: {' '.join(cmd)}")
                    
                    # Set up environment for SSH if needed
                    env = os.environ.copy()
                    if ssh_key_path and repo_url.startswith('git@'):
                        env['GIT_SSH_COMMAND'] = f'ssh -i {ssh_key_path} -o StrictHostKeyChecking=no'
                        logger.info(f"Using SSH command: {env['GIT_SSH_COMMAND']}")
                        # Force print to ensure we see this even if logger is swallowed
                        print(f"🔧 SSH Command: {env['GIT_SSH_COMMAND']}")
                    
                    logger.info(f"Starting git clone with timeout=600s")
                    print(f"🔧 Starting git clone: {' '.join(cmd)}")
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env, timeout=600)
                    if result.stdout:
                        logger.info(f"Git stdout: {result.stdout.strip()}")
                    if result.stderr:
                        logger.info(f"Git stderr: {result.stderr.strip()}")
                    logger.info("Git clone with branch succeeded")
                    return f"Successfully cloned {repo_url} to {local_path} on branch {branch}"
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Git clone with branch failed: {e.stderr}")
                    # If branch doesn't exist, fall back to default branch
                    pass
            
            # Clone without specifying branch (uses repository's default branch)
            cmd = ['git', 'clone', repo_url, local_path]
            logger.info(f"Executing git command: {' '.join(cmd)}")
            
            # Set up environment for SSH if needed
            env = os.environ.copy()
            if ssh_key_path and repo_url.startswith('git@'):
                env['GIT_SSH_COMMAND'] = f'ssh -i {ssh_key_path} -o StrictHostKeyChecking=no'
                logger.info(f"Using SSH command: {env['GIT_SSH_COMMAND']}")
                # Force print to ensure we see this even if logger is swallowed
                print(f"🔧 SSH Command: {env['GIT_SSH_COMMAND']}")
            
            logger.info(f"Starting git clone with timeout=600s")
            print(f"🔧 Starting git clone: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env, timeout=600)
            if result.stdout:
                logger.info(f"Git stdout: {result.stdout.strip()}")
            if result.stderr:
                logger.info(f"Git stderr: {result.stderr.strip()}")
            logger.info("Git clone succeeded")
            return f"Successfully cloned {repo_url} to {local_path}"
        
    except subprocess.TimeoutExpired as e:
        error_msg = f"Git clone timed out after 600 seconds"
        if e.stderr:
            error_msg += f"\nSTDERR: {e.stderr.strip()}"
        if e.stdout:
            error_msg += f"\nSTDOUT: {e.stdout.strip()}"
        
        logger.error(f"Git clone timeout: {error_msg}")
        print(f"❌ Git clone TIMEOUT: {error_msg}")
        
        # Add timeout-specific troubleshooting hints
        error_msg += f"\n\n🔧 Timeout Troubleshooting Tips:"
        error_msg += f"\n- Repository might be very large, consider shallow clone"
        error_msg += f"\n- Network might be slow, try again later"
        error_msg += f"\n- Check if repository exists: ssh -T -i {ssh_key_path} git@{default_host}"
        
        return f"❌ Clone timeout: {error_msg}"
    except subprocess.CalledProcessError as e:
        error_msg = f"Git command failed with exit code {e.returncode}"
        if e.stderr:
            error_msg += f"\nSTDERR: {e.stderr.strip()}"
        if e.stdout:
            error_msg += f"\nSTDOUT: {e.stdout.strip()}"
        
        logger.error(f"Git clone failed: {error_msg}")
        print(f"❌ Git clone FAILED: {error_msg}")
        
        # Add specific SSH troubleshooting hints
        if repo_url.startswith('git@') and "Permission denied" in str(e.stderr):
            error_msg += f"\n\n🔧 SSH Troubleshooting Tips:"
            error_msg += f"\n- SSH Key Path: {ssh_key_path}"
            error_msg += f"\n- Test SSH connection: ssh -T -i {ssh_key_path} git@{default_host}"
            error_msg += f"\n- Check key permissions: ls -la {ssh_key_path}"
            error_msg += f"\n- Verify host key: ssh-keyscan {default_host}"
        
        return f"❌ Error cloning repository: {error_msg}"
    except Exception as e:
        logger.error(f"Unexpected error in clone_github_repo_shared: {str(e)}")
        return f"❌ Unexpected error: {str(e)}"
    finally:
        logger.tool_end("clone_github_repo_shared")