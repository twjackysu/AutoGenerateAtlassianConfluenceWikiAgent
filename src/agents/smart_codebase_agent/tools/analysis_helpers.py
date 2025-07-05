import os
import re
from typing import List, Dict, Any


def get_architecture_analysis(files: List[str], repo_path: str) -> str:
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


def get_data_sources_analysis(files: List[str], repo_path: str) -> str:
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


def get_dependencies_analysis(files: List[str], repo_path: str) -> str:
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


def get_overview_analysis(files: List[str], repo_path: str) -> str:
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