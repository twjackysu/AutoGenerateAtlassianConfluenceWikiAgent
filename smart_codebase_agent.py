import os
import subprocess
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import fnmatch
import re
from agents import Agent, function_tool
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


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


@function_tool
async def analyze_codebase_smart(
    repo_path: str,
    analysis_focus: str = "comprehensive"
) -> str:
    """
    Intelligently analyze a codebase, automatically determining if chunking is needed based on size.
    
    Args:
        repo_path: Path to the repository
        analysis_focus: Focus area ('architecture', 'data_sources', 'dependencies', 'overview', 'comprehensive')
    
    Returns:
        Markdown documentation of the analysis
    """
    try:
        if not os.path.exists(repo_path):
            return f"## Error\nRepository path does not exist: {repo_path}"
        
        # Get all relevant files and assess size
        files = []
        total_size = 0
        
        for root, dirs, file_names in os.walk(repo_path):
            # Skip common directories that don't need analysis
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build']]
            
            for file_name in file_names:
                if file_name.endswith(('.py', '.js', '.ts', '.java', '.go', '.php', '.cpp', '.c', '.rs', '.rb', '.cs')):
                    file_path = os.path.join(root, file_name)
                    files.append(file_path)
                    try:
                        total_size += os.path.getsize(file_path)
                    except:
                        pass
        
        repo_name = os.path.basename(repo_path)
        
        # Determine analysis strategy based on size
        file_count = len(files)
        
        if file_count == 0:
            return f"# {repo_name} Analysis\n\n⚠️ No source code files found for analysis."
        
        # Auto-determine analysis approach
        if file_count <= 20 and total_size < 500000:  # Small project
            return _analyze_small_project(files, repo_path, analysis_focus)
        elif file_count <= 100 and total_size < 2000000:  # Medium project  
            return _analyze_medium_project(files, repo_path, analysis_focus)
        else:  # Large project - need summary approach
            return _analyze_large_project(files, repo_path, analysis_focus)
            
    except Exception as e:
        return f"## Error in Analysis\n{str(e)}"


def _analyze_small_project(files: List[str], repo_path: str, focus: str) -> str:
    """Analyze small projects comprehensively"""
    
    repo_name = os.path.basename(repo_path)
    markdown = f"# {repo_name} - Complete Analysis\n\n"
    markdown += f"📊 **Project Size**: {len(files)} files (Small project - comprehensive analysis)\n\n"
    
    # Comprehensive analysis for small projects
    if focus in ["comprehensive", "architecture"]:
        markdown += _get_architecture_analysis(files, repo_path)
    
    if focus in ["comprehensive", "data_sources"]:
        markdown += _get_data_sources_analysis(files, repo_path)
    
    if focus in ["comprehensive", "dependencies"]:
        markdown += _get_dependencies_analysis(files, repo_path)
    
    if focus in ["comprehensive", "overview"]:
        markdown += _get_overview_analysis(files, repo_path)
    
    return markdown


def _analyze_medium_project(files: List[str], repo_path: str, focus: str) -> str:
    """Analyze medium projects with focused approach"""
    
    repo_name = os.path.basename(repo_path)
    markdown = f"# {repo_name} - Focused Analysis\n\n"
    markdown += f"📊 **Project Size**: {len(files)} files (Medium project - focused analysis)\n\n"
    
    # Focused analysis for medium projects
    if focus == "architecture":
        markdown += _get_architecture_analysis(files, repo_path)
    elif focus == "data_sources":
        markdown += _get_data_sources_analysis(files, repo_path)
    elif focus == "dependencies":
        markdown += _get_dependencies_analysis(files, repo_path)
    else:  # comprehensive or overview
        markdown += _get_overview_analysis(files, repo_path)
        markdown += "\n---\n\n"
        markdown += "💡 **Note**: For detailed analysis of this medium-sized project, request specific focus areas:\n"
        markdown += "- Architecture analysis\n- Data sources analysis\n- Dependencies analysis\n\n"
    
    return markdown


def _analyze_large_project(files: List[str], repo_path: str, focus: str) -> str:
    """Analyze large projects with summary approach"""
    
    repo_name = os.path.basename(repo_path)
    markdown = f"# {repo_name} - Summary Analysis\n\n"
    markdown += f"📊 **Project Size**: {len(files)} files (Large project - summary approach)\n\n"
    
    # High-level summary for large projects
    markdown += _get_overview_analysis(files, repo_path)
    
    markdown += "\n---\n\n"
    markdown += "## 🎯 Recommended Next Steps\n\n"
    markdown += "This is a large project. For detailed analysis, consider:\n\n"
    markdown += "1. **Focus on specific directories**: Analyze key modules separately\n"
    markdown += "2. **Targeted analysis**: Request analysis of specific aspects:\n"
    markdown += "   - `analyze_codebase_smart('./path', 'architecture')`\n"
    markdown += "   - `analyze_codebase_smart('./path', 'data_sources')`\n"
    markdown += "   - `analyze_codebase_smart('./path', 'dependencies')`\n\n"
    
    # Show directory structure to help with targeted analysis
    markdown += "### 📁 Directory Structure (for targeted analysis)\n\n"
    dirs = set()
    for file_path in files[:50]:  # Sample first 50 files
        rel_path = os.path.relpath(file_path, repo_path)
        dirs.add(os.path.dirname(rel_path))
    
    for directory in sorted(dirs):
        if directory:
            markdown += f"- `{directory}/`\n"
    
    return markdown


def _get_architecture_analysis(files: List[str], repo_path: str) -> str:
    """Get architecture analysis"""
    
    markdown = "## 🏗️ Architecture Analysis\n\n"
    
    frameworks = set()
    patterns = set()
    components = {}
    
    # Sample files to avoid token limits
    sample_files = files[:30] if len(files) > 30 else files
    
    for file_path in sample_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                rel_path = os.path.relpath(file_path, repo_path)
                
                # Detect frameworks
                framework_indicators = {
                    'Django': ['django', 'models.model', 'views.view'],
                    'Flask': ['flask', 'app.route', '@app.route'],
                    'React': ['react', 'usestate', 'useeffect', 'jsx'],
                    'Express': ['express', 'app.get', 'app.post'],
                    'Spring': ['springframework', '@controller', '@service'],
                    'FastAPI': ['fastapi', 'from fastapi'],
                    'Vue': ['vue', 'vue.js', '@vue'],
                    'Angular': ['angular', '@angular', '@component']
                }
                
                for framework, indicators in framework_indicators.items():
                    if any(indicator in content for indicator in indicators):
                        frameworks.add(framework)
                
                # Detect patterns
                if 'controller' in rel_path.lower():
                    patterns.add('MVC Pattern')
                if 'service' in rel_path.lower():
                    patterns.add('Service Layer')
                if 'repository' in rel_path.lower():
                    patterns.add('Repository Pattern')
                if 'api' in rel_path.lower():
                    patterns.add('API Layer')
                
                # Count component types
                if 'controller' in rel_path.lower():
                    components['Controllers'] = components.get('Controllers', 0) + 1
                elif 'model' in rel_path.lower():
                    components['Models'] = components.get('Models', 0) + 1
                elif 'service' in rel_path.lower():
                    components['Services'] = components.get('Services', 0) + 1
                elif 'view' in rel_path.lower():
                    components['Views'] = components.get('Views', 0) + 1
                else:
                    components['Other'] = components.get('Other', 0) + 1
        
        except Exception:
            continue
    
    # Generate framework section
    if frameworks:
        markdown += "### 🔧 Detected Frameworks\n"
        for framework in sorted(frameworks):
            markdown += f"- **{framework}**\n"
        markdown += "\n"
    
    # Generate patterns section
    if patterns:
        markdown += "### 📐 Architecture Patterns\n"
        for pattern in sorted(patterns):
            markdown += f"- {pattern}\n"
        markdown += "\n"
    
    # Generate components section
    if components:
        markdown += "### 📦 Component Distribution\n"
        for comp_type, count in sorted(components.items()):
            markdown += f"- **{comp_type}**: {count} files\n"
        markdown += "\n"
    
    return markdown


def _get_data_sources_analysis(files: List[str], repo_path: str) -> str:
    """Get data sources analysis"""
    
    markdown = "## 💾 Data Sources Analysis\n\n"
    
    databases = []
    apis = []
    cloud_services = []
    
    # Sample files to avoid token limits
    sample_files = files[:25] if len(files) > 25 else files
    
    for file_path in sample_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(file_path, repo_path)
                
                # Database detection
                db_patterns = {
                    'PostgreSQL': [r'postgresql://', r'psycopg2', r'pg_'],
                    'MySQL': [r'mysql://', r'pymysql', r'mysql.connector'],
                    'MongoDB': [r'mongodb://', r'pymongo', r'mongoose'],
                    'Redis': [r'redis://', r'import redis', r'redis.Redis'],
                    'SQLite': [r'sqlite:///', r'sqlite3']
                }
                
                for db_type, patterns in db_patterns.items():
                    if any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns):
                        if db_type not in [db['type'] for db in databases]:
                            databases.append({'type': db_type, 'file': rel_path})
                
                # API detection
                api_patterns = [
                    r'https?://api\.',
                    r'requests\.(?:get|post|put|delete)',
                    r'fetch\(',
                    r'axios\.',
                    r'@app\.route',
                    r'@api\.route'
                ]
                
                for pattern in api_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        apis.append({'pattern': pattern, 'file': rel_path})
                        break
                
                # Cloud services detection
                cloud_patterns = {
                    'AWS': [r'amazonaws\.com', r'boto3', r's3://'],
                    'Azure': [r'azure\.com', r'azure-', r'microsoft.com'],
                    'Google Cloud': [r'googleapis\.com', r'google-cloud', r'gcp'],
                    'Firebase': [r'firebase', r'firestore']
                }
                
                for service, patterns in cloud_patterns.items():
                    if any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns):
                        if service not in [cs['service'] for cs in cloud_services]:
                            cloud_services.append({'service': service, 'file': rel_path})
        
        except Exception:
            continue
    
    # Generate sections
    if databases:
        markdown += "### 🗄️ Database Systems\n"
        for db in databases:
            markdown += f"- **{db['type']}** (detected in {db['file']})\n"
        markdown += "\n"
    
    if apis:
        unique_files = list(set(api['file'] for api in apis))
        markdown += f"### 🌐 API Integration\n"
        markdown += f"API usage detected in {len(unique_files)} files\n\n"
    
    if cloud_services:
        markdown += "### ☁️ Cloud Services\n"
        for cs in cloud_services:
            markdown += f"- **{cs['service']}** (detected in {cs['file']})\n"
        markdown += "\n"
    
    if not databases and not apis and not cloud_services:
        markdown += "No obvious data sources detected in the analyzed files.\n\n"
    
    return markdown


def _get_dependencies_analysis(files: List[str], repo_path: str) -> str:
    """Get dependencies analysis"""
    
    markdown = "## 📦 Dependencies Analysis\n\n"
    
    # Check for dependency files
    dep_files = ['requirements.txt', 'package.json', 'pyproject.toml', 'Pipfile', 'pom.xml', 'build.gradle']
    found_dep_files = []
    
    for dep_file in dep_files:
        dep_path = os.path.join(repo_path, dep_file)
        if os.path.exists(dep_path):
            found_dep_files.append(dep_file)
    
    if found_dep_files:
        markdown += "### 📋 Dependency Files Found\n"
        for dep_file in found_dep_files:
            markdown += f"- `{dep_file}`\n"
        markdown += "\n"
        
        # Analyze package.json if exists
        package_json_path = os.path.join(repo_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                import json
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    
                deps = package_data.get('dependencies', {})
                dev_deps = package_data.get('devDependencies', {})
                
                markdown += f"### 📦 NPM Dependencies\n"
                markdown += f"- **Production dependencies**: {len(deps)}\n"
                markdown += f"- **Development dependencies**: {len(dev_deps)}\n\n"
                
                if deps:
                    markdown += "#### Key Production Dependencies\n"
                    for dep in list(deps.keys())[:10]:
                        markdown += f"- `{dep}`\n"
                    markdown += "\n"
            except:
                pass
        
        # Analyze requirements.txt if exists
        req_path = os.path.join(repo_path, 'requirements.txt')
        if os.path.exists(req_path):
            try:
                with open(req_path, 'r') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
                    
                markdown += f"### 🐍 Python Dependencies\n"
                markdown += f"- **Total packages**: {len(lines)}\n\n"
                
                if lines:
                    markdown += "#### Key Dependencies\n"
                    for line in lines[:10]:
                        pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0]
                        markdown += f"- `{pkg_name}`\n"
                    markdown += "\n"
            except:
                pass
    
    # Analyze import patterns in code
    external_imports = set()
    sample_files = files[:20] if len(files) > 20 else files
    
    for file_path in sample_files:
        if file_path.endswith('.py'):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Find external imports
                    import_patterns = [
                        r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                        r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import'
                    ]
                    
                    for pattern in import_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if not match.startswith('.') and match not in ['os', 'sys', 'json', 're', 'datetime']:
                                external_imports.add(match)
            except:
                continue
    
    if external_imports:
        markdown += f"### 🔗 Detected Imports\n"
        for imp in sorted(list(external_imports)[:15]):
            markdown += f"- `{imp}`\n"
        markdown += "\n"
    
    return markdown


def _get_overview_analysis(files: List[str], repo_path: str) -> str:
    """Get overview analysis"""
    
    markdown = "## 📋 Project Overview\n\n"
    
    # File statistics
    file_types = {}
    total_size = 0
    
    for file_path in files:
        ext = os.path.splitext(file_path)[1] or 'no extension'
        file_types[ext] = file_types.get(ext, 0) + 1
        try:
            total_size += os.path.getsize(file_path)
        except:
            pass
    
    markdown += f"### 📊 Statistics\n"
    markdown += f"- **Total files analyzed**: {len(files)}\n"
    markdown += f"- **Total size**: {total_size // 1024:.1f} KB\n"
    markdown += f"- **File types**: {len(file_types)}\n\n"
    
    markdown += f"### 📁 File Type Distribution\n"
    for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
        markdown += f"- **{ext}**: {count} files\n"
    markdown += "\n"
    
    # Directory structure
    directories = set()
    for file_path in files:
        rel_path = os.path.relpath(file_path, repo_path)
        directory = os.path.dirname(rel_path)
        if directory:
            directories.add(directory)
    
    markdown += f"### 📂 Directory Structure\n"
    for directory in sorted(directories)[:15]:
        markdown += f"- `{directory}/`\n"
    
    if len(directories) > 15:
        markdown += f"- ... and {len(directories) - 15} more directories\n"
    
    markdown += "\n"
    
    return markdown


# Create the Smart Codebase Agent
smart_codebase_agent = Agent(
    name="SmartCodebaseAgent",
    instructions="""
    You are an intelligent codebase analysis agent that automatically adapts your analysis approach based on project size and complexity.
    
    **Automatic Intelligence**:
    - Automatically assess codebase size and complexity
    - Choose appropriate analysis depth to stay within token limits
    - Provide comprehensive analysis for small projects
    - Focus on key insights for medium projects  
    - Generate high-level summaries for large projects
    
    **Your capabilities**:
    1. Clone GitHub repositories
    2. Intelligently analyze codebases with automatic size detection
    3. Generate focused markdown documentation
    4. Provide actionable recommendations for further analysis
    
    **Analysis Strategy**:
    - **Small projects** (≤20 files): Comprehensive analysis of architecture, data sources, and dependencies
    - **Medium projects** (21-100 files): Focused analysis on requested area with overview
    - **Large projects** (>100 files): High-level summary with recommendations for targeted analysis
    
    **When users request analysis**:
    1. Clone repository if needed
    2. Automatically assess project size
    3. Apply appropriate analysis strategy
    4. Generate useful markdown documentation
    5. Suggest next steps if needed
    
    **Always provide**:
    - Clear, structured markdown output
    - Actionable insights based on project size
    - Specific recommendations for large projects
    - Focus on practical information developers need
    
    Be smart about token usage while maximizing value to the user.
    """,
    tools=[clone_github_repo, analyze_codebase_smart]
)


# Example usage
async def example_smart_analysis():
    """Example of smart codebase analysis"""
    from agents import Runner
    
    result = await Runner.run(
        smart_codebase_agent,
        "Please analyze the repository './repos/JackyAIApp' and provide insights about its architecture and data sources."
    )
    
    print("Smart analysis result:", result.final_output)


if __name__ == "__main__":
    asyncio.run(example_smart_analysis())