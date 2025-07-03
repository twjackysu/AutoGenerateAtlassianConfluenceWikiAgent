"""
Codebase Analysis Agent - Responsible for analyzing code structure and dependencies
"""
import asyncio
import ast
import json
from typing import List, Dict, Optional, Any, Set
from pathlib import Path
import tree_sitter
from tree_sitter import Language, Parser
from agents import Agent, Tool
from src.models.claude_model import ClaudeModel
from src.config import config

class CodebaseAnalysisAgent:
    """Agent responsible for analyzing codebase structure and dependencies"""
    
    def __init__(self):
        self.agent = Agent(
            name="Codebase Analysis Agent",
            instructions="""
            You are a codebase analysis specialist. Your responsibilities include:
            1. Analyzing code structure, dependencies, and relationships
            2. Identifying functions, classes, APIs, and data flows
            3. Extracting architecture patterns and design decisions
            4. Mapping data sources and external dependencies
            5. Generating comprehensive code summaries
            6. Identifying entry points and main execution flows
            
            Provide detailed analysis that helps understand the codebase structure,
            its components, and how they interact with each other.
            """,
            model=ClaudeModel(),
            tools=[
                Tool(
                    name="analyze_python_file",
                    description="Analyze a Python file using AST parsing",
                    function=self.analyze_python_file
                ),
                Tool(
                    name="analyze_javascript_file", 
                    description="Analyze a JavaScript/TypeScript file",
                    function=self.analyze_javascript_file
                ),
                Tool(
                    name="extract_dependencies",
                    description="Extract dependencies from various file types",
                    function=self.extract_dependencies
                ),
                Tool(
                    name="analyze_project_structure",
                    description="Analyze overall project structure and architecture",
                    function=self.analyze_project_structure
                ),
                Tool(
                    name="identify_api_endpoints",
                    description="Identify API endpoints and routes",
                    function=self.identify_api_endpoints
                ),
                Tool(
                    name="map_data_flows",
                    description="Map data flows and transformations",
                    function=self.map_data_flows
                )
            ]
        )
    
    async def analyze_python_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze a Python file using AST parsing"""
        try:
            tree = ast.parse(content)
            analysis = {
                "file_path": file_path,
                "language": "python",
                "classes": [],
                "functions": [],
                "imports": [],
                "variables": [],
                "decorators": [],
                "docstrings": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                        "bases": [self._get_name(base) for base in node.bases],
                        "docstring": ast.get_docstring(node)
                    }
                    analysis["classes"].append(class_info)
                
                elif isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "decorators": [self._get_name(dec) for dec in node.decorator_list],
                        "docstring": ast.get_docstring(node),
                        "is_async": isinstance(node, ast.AsyncFunctionDef)
                    }
                    analysis["functions"].append(func_info)
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            analysis["imports"].append({
                                "module": alias.name,
                                "alias": alias.asname,
                                "type": "import"
                            })
                    else:
                        module = node.module or ""
                        for alias in node.names:
                            analysis["imports"].append({
                                "module": module,
                                "name": alias.name,
                                "alias": alias.asname,
                                "type": "from_import"
                            })
            
            return {
                "status": "success",
                "analysis": analysis
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to analyze Python file: {str(e)}"
            }
    
    def _get_name(self, node):
        """Extract name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return str(node)
    
    async def analyze_javascript_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze a JavaScript/TypeScript file"""
        try:
            # Basic regex-based analysis for JavaScript/TypeScript
            # In a real implementation, you'd use tree-sitter for proper parsing
            analysis = {
                "file_path": file_path,
                "language": "javascript" if file_path.endswith('.js') else "typescript",
                "functions": [],
                "classes": [],
                "imports": [],
                "exports": [],
                "variables": []
            }
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                # Find imports
                if line.startswith('import ') or line.startswith('const ') and 'require(' in line:
                    analysis["imports"].append({
                        "line": i,
                        "statement": line
                    })
                
                # Find exports
                if line.startswith('export ') or line.startswith('module.exports'):
                    analysis["exports"].append({
                        "line": i,
                        "statement": line
                    })
                
                # Find function definitions
                if 'function ' in line or '=>' in line:
                    analysis["functions"].append({
                        "line": i,
                        "statement": line
                    })
                
                # Find class definitions
                if line.startswith('class '):
                    analysis["classes"].append({
                        "line": i,
                        "statement": line
                    })
            
            return {
                "status": "success",
                "analysis": analysis
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to analyze JavaScript file: {str(e)}"
            }
    
    async def extract_dependencies(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract dependencies from project files"""
        try:
            dependencies = {
                "python": {
                    "imports": set(),
                    "pip_packages": set()
                },
                "javascript": {
                    "imports": set(),
                    "npm_packages": set()
                },
                "other": set()
            }
            
            for file_data in files_data:
                file_path = file_data.get("path", "")
                content = file_data.get("content", "")
                
                if file_path.endswith('.py'):
                    await self._extract_python_dependencies(content, dependencies["python"])
                elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
                    await self._extract_js_dependencies(content, dependencies["javascript"])
                elif file_path.endswith(('requirements.txt', 'package.json', 'Pipfile')):
                    await self._extract_package_dependencies(file_path, content, dependencies)
            
            # Convert sets to lists for JSON serialization
            result = {}
            for lang, deps in dependencies.items():
                if isinstance(deps, dict):
                    result[lang] = {k: list(v) for k, v in deps.items()}
                else:
                    result[lang] = list(deps)
            
            return {
                "status": "success",
                "dependencies": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to extract dependencies: {str(e)}"
            }
    
    async def _extract_python_dependencies(self, content: str, deps: Dict[str, Set]):
        """Extract Python dependencies"""
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        deps["imports"].add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        deps["imports"].add(node.module.split('.')[0])
        except:
            pass
    
    async def _extract_js_dependencies(self, content: str, deps: Dict[str, Set]):
        """Extract JavaScript/TypeScript dependencies"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('import ') and 'from ' in line:
                parts = line.split('from ')
                if len(parts) > 1:
                    module = parts[1].strip().strip('\'"').strip(';')
                    deps["imports"].add(module)
    
    async def _extract_package_dependencies(self, file_path: str, content: str, deps: Dict):
        """Extract dependencies from package files"""
        if file_path.endswith('requirements.txt'):
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    package = line.split('==')[0].split('>=')[0].split('<=')[0]
                    deps["python"]["pip_packages"].add(package)
        elif file_path.endswith('package.json'):
            try:
                package_data = json.loads(content)
                for dep_type in ['dependencies', 'devDependencies']:
                    if dep_type in package_data:
                        for package in package_data[dep_type].keys():
                            deps["javascript"]["npm_packages"].add(package)
            except:
                pass
    
    async def analyze_project_structure(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall project structure and architecture"""
        try:
            structure = {
                "project_type": "unknown",
                "frameworks": [],
                "languages": {},
                "entry_points": [],
                "config_files": [],
                "test_files": [],
                "documentation": [],
                "directory_structure": {}
            }
            
            # Analyze files
            for file_data in files_data:
                file_path = file_data.get("path", "")
                path_obj = Path(file_path)
                
                # Count languages
                ext = path_obj.suffix.lower()
                if ext:
                    structure["languages"][ext] = structure["languages"].get(ext, 0) + 1
                
                # Identify special files
                filename = path_obj.name.lower()
                
                if filename in ['main.py', 'app.py', 'index.js', 'main.js', 'server.js']:
                    structure["entry_points"].append(file_path)
                elif filename in ['package.json', 'requirements.txt', 'pyproject.toml', 'setup.py']:
                    structure["config_files"].append(file_path)
                elif 'test' in filename or filename.startswith('test_'):
                    structure["test_files"].append(file_path)
                elif filename in ['readme.md', 'readme.txt', 'docs']:
                    structure["documentation"].append(file_path)
            
            # Determine project type
            if any(f.endswith('package.json') for f in structure["config_files"]):
                structure["project_type"] = "node.js"
            elif any(f.endswith(('.py', 'requirements.txt', 'pyproject.toml')) for f in structure["config_files"]):
                structure["project_type"] = "python"
            
            return {
                "status": "success",
                "structure": structure
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to analyze project structure: {str(e)}"
            }
    
    async def identify_api_endpoints(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify API endpoints and routes"""
        try:
            endpoints = []
            
            for file_data in files_data:
                content = file_data.get("content", "")
                file_path = file_data.get("path", "")
                
                # Look for common API patterns
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    
                    # Flask/FastAPI patterns
                    if any(decorator in line for decorator in ['@app.route', '@router.', '@api.']):
                        endpoints.append({
                            "file": file_path,
                            "line": i,
                            "endpoint": line,
                            "framework": "flask/fastapi"
                        })
                    
                    # Express.js patterns
                    elif any(method in line for method in ['app.get(', 'app.post(', 'app.put(', 'app.delete(']):
                        endpoints.append({
                            "file": file_path,
                            "line": i,
                            "endpoint": line,
                            "framework": "express"
                        })
            
            return {
                "status": "success",
                "endpoints": endpoints
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to identify API endpoints: {str(e)}"
            }
    
    async def map_data_flows(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Map data flows and transformations"""
        try:
            data_flows = {
                "database_connections": [],
                "api_calls": [],
                "file_operations": [],
                "data_transformations": []
            }
            
            for file_data in files_data:
                content = file_data.get("content", "")
                file_path = file_data.get("path", "")
                
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    line_lower = line.lower().strip()
                    
                    # Database patterns
                    if any(db in line_lower for db in ['connect(', 'session.', 'query(', 'execute(']):
                        data_flows["database_connections"].append({
                            "file": file_path,
                            "line": i,
                            "statement": line.strip()
                        })
                    
                    # API call patterns
                    elif any(api in line_lower for api in ['requests.', 'fetch(', 'axios.', 'http.']):
                        data_flows["api_calls"].append({
                            "file": file_path,
                            "line": i,
                            "statement": line.strip()
                        })
                    
                    # File operations
                    elif any(file_op in line_lower for file_op in ['open(', 'read(', 'write(', 'fs.']):
                        data_flows["file_operations"].append({
                            "file": file_path,
                            "line": i,
                            "statement": line.strip()
                        })
            
            return {
                "status": "success",
                "data_flows": data_flows
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to map data flows: {str(e)}"
            }
