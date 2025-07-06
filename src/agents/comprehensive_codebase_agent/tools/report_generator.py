import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from agents import function_tool

from .context_manager import get_context_manager


class ReportTemplate(Enum):
    """Predefined report templates"""
    API_INVENTORY = "api_inventory"
    DATA_FLOW = "data_flow"
    ARCHITECTURE_OVERVIEW = "architecture_overview"
    DATABASE_SCHEMA = "database_schema"
    SECURITY_ANALYSIS = "security_analysis"
    DEPENDENCY_MAP = "dependency_map"


@dataclass
class ReportSection:
    """A section within a report"""
    title: str
    content: str
    order: int
    section_type: str  # "overview", "details", "table", "list"


class ReportGenerator:
    """Generates structured markdown reports from analysis context"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.context_manager = get_context_manager(session_id)
    
    def generate_api_inventory_report(self) -> str:
        """Generate comprehensive API inventory report"""
        context = self.context_manager.context
        apis = context.discovered_apis
        
        if not apis:
            return self._generate_empty_report("API Inventory", "No APIs discovered in the codebase.")
        
        # Group APIs by method and source file
        apis_by_method = {}
        apis_by_file = {}
        
        for api in apis:
            method = api.get('method', 'UNKNOWN')
            source_file = api.get('source_file', 'unknown')
            
            if method not in apis_by_method:
                apis_by_method[method] = []
            apis_by_method[method].append(api)
            
            if source_file not in apis_by_file:
                apis_by_file[source_file] = []
            apis_by_file[source_file].append(api)
        
        # Generate report
        report = f"""# 🚀 API Inventory Report

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for session {self.session_id}*

## 📊 Summary Statistics
- **Total API Endpoints**: {len(apis)}
- **Unique Files with APIs**: {len(apis_by_file)}
- **HTTP Methods Used**: {len(apis_by_method)}

## 📋 API Endpoints by Method

"""
        
        # APIs by method
        for method in sorted(apis_by_method.keys()):
            method_apis = apis_by_method[method]
            report += f"### {method} Endpoints ({len(method_apis)})\n\n"
            
            for api in sorted(method_apis, key=lambda x: x.get('path', '')):
                path = api.get('path', 'Unknown path')
                source = api.get('source_file', 'Unknown file')
                description = api.get('description', 'No description')
                parameters = api.get('parameters', [])
                
                report += f"#### `{method} {path}`\n"
                report += f"- **Source**: `{source}`\n"
                if description != 'No description':
                    report += f"- **Description**: {description}\n"
                
                if parameters:
                    report += f"- **Parameters**: {', '.join(f'`{p}`' for p in parameters)}\n"
                
                report += "\n"
        
        # APIs by file
        report += f"## 📁 API Endpoints by File\n\n"
        
        for file_path in sorted(apis_by_file.keys()):
            file_apis = apis_by_file[file_path]
            report += f"### `{file_path}` ({len(file_apis)} endpoints)\n\n"
            
            for api in sorted(file_apis, key=lambda x: (x.get('method', ''), x.get('path', ''))):
                method = api.get('method', 'UNKNOWN')
                path = api.get('path', 'Unknown path')
                report += f"- **{method}** `{path}`\n"
            
            report += "\n"
        
        # Implementation patterns
        frameworks = context.framework_usage
        if frameworks:
            report += f"## 🏗️ API Framework Usage\n\n"
            for framework, usages in frameworks.items():
                if any('api' in usage.lower() or 'endpoint' in usage.lower() or 'route' in usage.lower() for usage in usages):
                    report += f"### {framework}\n"
                    api_usages = [u for u in usages if 'api' in u.lower() or 'endpoint' in u.lower() or 'route' in u.lower()]
                    for usage in api_usages[:5]:  # Show top 5
                        report += f"- {usage}\n"
                    report += "\n"
        
        return report
    
    def generate_data_flow_report(self) -> str:
        """Generate data flow analysis report"""
        context = self.context_manager.context
        
        # Analyze data flow from imports, functions, and databases
        imports = context.discovered_imports
        functions = context.discovered_functions
        databases = context.discovered_databases
        file_deps = context.file_dependencies
        
        report = f"""# 🌊 Data Flow Analysis Report

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for session {self.session_id}*

## 📊 Data Flow Overview
- **Database Connections**: {len(databases)}
- **Data Processing Functions**: {len([f for f in functions if any(keyword in f.get('name', '').lower() for keyword in ['process', 'transform', 'parse', 'convert', 'handle'])])}
- **File Dependencies**: {len(file_deps)}
- **Import Relationships**: {len(imports)}

"""
        
        # Database connections
        if databases:
            report += f"## 💾 Database Connections\n\n"
            db_types = {}
            for db in databases:
                db_type = db.get('type', 'Unknown')
                source_file = db.get('source_file', 'Unknown')
                
                if db_type not in db_types:
                    db_types[db_type] = []
                db_types[db_type].append(source_file)
            
            for db_type, files in db_types.items():
                report += f"### {db_type}\n"
                report += f"**Files using this database**: {len(set(files))}\n\n"
                for file_path in sorted(set(files)):
                    report += f"- `{file_path}`\n"
                report += "\n"
        
        # Data processing functions
        data_functions = [
            f for f in functions 
            if any(keyword in f.get('name', '').lower() for keyword in ['process', 'transform', 'parse', 'convert', 'handle', 'fetch', 'save', 'load'])
        ]
        
        if data_functions:
            report += f"## ⚙️ Data Processing Functions ({len(data_functions)})\n\n"
            
            # Group by file
            functions_by_file = {}
            for func in data_functions:
                source_file = func.get('source_file', 'Unknown')
                if source_file not in functions_by_file:
                    functions_by_file[source_file] = []
                functions_by_file[source_file].append(func)
            
            for file_path in sorted(functions_by_file.keys()):
                file_functions = functions_by_file[file_path]
                report += f"### `{file_path}`\n\n"
                
                for func in sorted(file_functions, key=lambda x: x.get('name', '')):
                    name = func.get('name', 'Unknown')
                    params = func.get('parameters', [])
                    return_type = func.get('return_type', 'Unknown')
                    
                    report += f"- **`{name}()`**\n"
                    if params:
                        report += f"  - Parameters: {', '.join(f'`{p}`' for p in params)}\n"
                    if return_type != 'Unknown':
                        report += f"  - Returns: `{return_type}`\n"
                
                report += "\n"
        
        # File dependency flow
        if file_deps:
            report += f"## 🔗 File Dependency Flow\n\n"
            
            # Find entry points (files that don't import from other local files)
            all_imported = set()
            for deps in file_deps.values():
                all_imported.update(deps)
            
            entry_points = [file for file in file_deps.keys() if file not in all_imported]
            
            if entry_points:
                report += f"### Entry Points ({len(entry_points)})\n"
                report += "Files that serve as entry points (not imported by others):\n\n"
                for entry in sorted(entry_points):
                    deps = file_deps.get(entry, [])
                    report += f"- `{entry}` → imports {len(deps)} modules\n"
                report += "\n"
            
            # Show most connected files
            most_connected = sorted(file_deps.items(), key=lambda x: len(x[1]), reverse=True)[:10]
            if most_connected:
                report += f"### Most Connected Files\n"
                report += "Files with the most dependencies:\n\n"
                for file_path, deps in most_connected:
                    report += f"- `{file_path}` → {len(deps)} dependencies\n"
                    for dep in deps[:3]:  # Show first 3 dependencies
                        report += f"  - `{dep}`\n"
                    if len(deps) > 3:
                        report += f"  - ... and {len(deps) - 3} more\n"
                report += "\n"
        
        return report
    
    def generate_architecture_overview_report(self) -> str:
        """Generate system architecture overview report"""
        context = self.context_manager.context
        
        patterns = context.detected_patterns
        frameworks = context.framework_usage
        file_deps = context.file_dependencies
        cross_refs = context.cross_references
        
        report = f"""# 🏗️ Architecture Overview Report

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for session {self.session_id}*

## 📊 Architecture Summary
- **Design Patterns Detected**: {len(patterns)}
- **Frameworks in Use**: {len(frameworks)}
- **File Dependencies**: {len(file_deps)}
- **Cross-References**: {len(cross_refs)}

"""
        
        # Framework analysis
        if frameworks:
            report += f"## 🛠️ Technology Stack\n\n"
            
            # Sort frameworks by usage count
            framework_usage = [(fw, len(usages)) for fw, usages in frameworks.items()]
            framework_usage.sort(key=lambda x: x[1], reverse=True)
            
            for framework, usage_count in framework_usage:
                report += f"### {framework} ({usage_count} usages)\n"
                
                # Analyze usage patterns
                usages = frameworks[framework]
                file_count = len(set(usage.split(':')[0] for usage in usages if ':' in usage))
                
                report += f"- **Files using this framework**: {file_count}\n"
                report += f"- **Total usage instances**: {usage_count}\n"
                
                # Show sample usages
                sample_usages = usages[:3]
                if sample_usages:
                    report += f"- **Example usages**:\n"
                    for usage in sample_usages:
                        report += f"  - {usage}\n"
                
                report += "\n"
        
        # Design patterns
        if patterns:
            report += f"## 🎨 Design Patterns\n\n"
            
            pattern_list = list(patterns)
            for pattern in sorted(pattern_list):
                report += f"- {pattern}\n"
            
            report += "\n"
        
        # Module structure analysis
        if file_deps:
            report += f"## 📁 Module Structure Analysis\n\n"
            
            # Analyze directory structure from file paths
            directories = {}
            for file_path in file_deps.keys():
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    directories[dir_path] = directories.get(dir_path, 0) + 1
            
            if directories:
                report += f"### Directory Distribution\n"
                sorted_dirs = sorted(directories.items(), key=lambda x: x[1], reverse=True)
                
                for dir_path, file_count in sorted_dirs[:10]:  # Top 10 directories
                    report += f"- `{dir_path}/`: {file_count} files\n"
                
                report += "\n"
            
            # Analyze coupling
            coupling_analysis = self._analyze_coupling(file_deps)
            if coupling_analysis:
                report += f"### Coupling Analysis\n"
                report += coupling_analysis
                report += "\n"
        
        # Component relationships
        if cross_refs:
            report += f"## 🔗 Component Relationships\n\n"
            
            # Find highly referenced components
            reference_counts = {}
            for from_file, refs in cross_refs.items():
                for ref in refs:
                    ref_file = ref.split(' (')[0]  # Remove relationship type
                    reference_counts[ref_file] = reference_counts.get(ref_file, 0) + 1
            
            most_referenced = sorted(reference_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            if most_referenced:
                report += f"### Most Referenced Components\n"
                for component, ref_count in most_referenced:
                    report += f"- `{component}`: referenced by {ref_count} other components\n"
                report += "\n"
        
        return report
    
    def generate_database_schema_report(self) -> str:
        """Generate database schema analysis report"""
        context = self.context_manager.context
        databases = context.discovered_databases
        functions = context.discovered_functions
        
        if not databases:
            return self._generate_empty_report("Database Schema", "No database connections discovered in the codebase.")
        
        report = f"""# 💾 Database Schema Analysis Report

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for session {self.session_id}*

## 📊 Database Overview
- **Database Connections**: {len(databases)}
- **Database-related Functions**: {len([f for f in functions if any(keyword in f.get('name', '').lower() for keyword in ['query', 'select', 'insert', 'update', 'delete', 'db', 'sql'])])}

"""
        
        # Group databases by type
        db_by_type = {}
        for db in databases:
            db_type = db.get('type', 'Unknown')
            if db_type not in db_by_type:
                db_by_type[db_type] = []
            db_by_type[db_type].append(db)
        
        # Database connections by type
        for db_type, db_list in db_by_type.items():
            report += f"## 🗄️ {db_type} Databases ({len(db_list)})\n\n"
            
            for i, db in enumerate(db_list, 1):
                source_file = db.get('source_file', 'Unknown')
                connection_string = db.get('connection_string', 'Not specified')
                tables = db.get('tables', [])
                
                report += f"### Database Connection {i}\n"
                report += f"- **Source File**: `{source_file}`\n"
                if connection_string != 'Not specified':
                    # Mask sensitive information in connection string
                    masked_connection = self._mask_connection_string(connection_string)
                    report += f"- **Connection**: `{masked_connection}`\n"
                
                if tables:
                    report += f"- **Tables**: {', '.join(f'`{table}`' for table in tables)}\n"
                
                report += "\n"
        
        # Database-related functions
        db_functions = [
            f for f in functions 
            if any(keyword in f.get('name', '').lower() for keyword in ['query', 'select', 'insert', 'update', 'delete', 'db', 'sql', 'execute'])
        ]
        
        if db_functions:
            report += f"## ⚙️ Database Functions ({len(db_functions)})\n\n"
            
            # Group by file
            functions_by_file = {}
            for func in db_functions:
                source_file = func.get('source_file', 'Unknown')
                if source_file not in functions_by_file:
                    functions_by_file[source_file] = []
                functions_by_file[source_file].append(func)
            
            for file_path in sorted(functions_by_file.keys()):
                file_functions = functions_by_file[file_path]
                report += f"### `{file_path}`\n\n"
                
                for func in sorted(file_functions, key=lambda x: x.get('name', '')):
                    name = func.get('name', 'Unknown')
                    description = func.get('description', '')
                    
                    report += f"- **`{name}()`**"
                    if description:
                        report += f": {description}"
                    report += "\n"
                
                report += "\n"
        
        return report
    
    def generate_security_analysis_report(self) -> str:
        """Generate security analysis report"""
        context = self.context_manager.context
        
        # Analyze for potential security issues
        functions = context.discovered_functions
        imports = context.discovered_imports
        apis = context.discovered_apis
        
        security_functions = [
            f for f in functions 
            if any(keyword in f.get('name', '').lower() for keyword in ['auth', 'login', 'password', 'token', 'encrypt', 'decrypt', 'hash', 'verify', 'validate'])
        ]
        
        security_imports = [
            i for i in imports 
            if any(keyword in i.get('module', '').lower() for keyword in ['crypto', 'hash', 'auth', 'jwt', 'bcrypt', 'security', 'ssl', 'tls'])
        ]
        
        auth_apis = [
            api for api in apis 
            if any(keyword in api.get('path', '').lower() for keyword in ['auth', 'login', 'logout', 'register', 'token', 'password'])
        ]
        
        report = f"""# 🔒 Security Analysis Report

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for session {self.session_id}*

## 📊 Security Overview
- **Security-related Functions**: {len(security_functions)}
- **Security-related Imports**: {len(security_imports)}
- **Authentication APIs**: {len(auth_apis)}

"""
        
        # Authentication APIs
        if auth_apis:
            report += f"## 🚪 Authentication Endpoints ({len(auth_apis)})\n\n"
            
            for api in sorted(auth_apis, key=lambda x: x.get('path', '')):
                method = api.get('method', 'UNKNOWN')
                path = api.get('path', 'Unknown')
                source = api.get('source_file', 'Unknown')
                
                report += f"- **{method}** `{path}` (in `{source}`)\n"
            
            report += "\n"
        
        # Security functions
        if security_functions:
            report += f"## 🔐 Security Functions ({len(security_functions)})\n\n"
            
            # Group by category
            function_categories = {
                'Authentication': ['auth', 'login', 'logout', 'verify'],
                'Encryption': ['encrypt', 'decrypt', 'hash', 'crypto'],
                'Validation': ['validate', 'sanitize', 'check'],
                'Token Management': ['token', 'jwt', 'session']
            }
            
            for category, keywords in function_categories.items():
                category_functions = [
                    f for f in security_functions
                    if any(keyword in f.get('name', '').lower() for keyword in keywords)
                ]
                
                if category_functions:
                    report += f"### {category} ({len(category_functions)})\n\n"
                    
                    for func in sorted(category_functions, key=lambda x: x.get('name', '')):
                        name = func.get('name', 'Unknown')
                        source = func.get('source_file', 'Unknown')
                        report += f"- `{name}()` in `{source}`\n"
                    
                    report += "\n"
        
        # Security libraries
        if security_imports:
            report += f"## 📚 Security Libraries ({len(security_imports)})\n\n"
            
            # Group by library
            libraries = {}
            for imp in security_imports:
                module = imp.get('module', 'Unknown')
                source = imp.get('source_file', 'Unknown')
                
                if module not in libraries:
                    libraries[module] = set()
                libraries[module].add(source)
            
            for library, files in libraries.items():
                report += f"### `{library}`\n"
                report += f"Used in {len(files)} files:\n\n"
                for file_path in sorted(files):
                    report += f"- `{file_path}`\n"
                report += "\n"
        
        # Security recommendations
        report += f"## 💡 Security Recommendations\n\n"
        
        if not security_functions and not security_imports:
            report += "⚠️ **Warning**: No explicit security mechanisms detected. Consider implementing:\n"
            report += "- Input validation and sanitization\n"
            report += "- Authentication and authorization\n"
            report += "- Encryption for sensitive data\n"
            report += "- Secure session management\n\n"
        
        if auth_apis and not security_functions:
            report += "⚠️ **Warning**: Authentication endpoints detected but no security functions found.\n"
            report += "Ensure proper authentication implementation.\n\n"
        
        report += "🔍 **Manual Review Recommended**: Automated analysis has limitations.\n"
        report += "Please conduct a thorough security review of the codebase.\n\n"
        
        return report
    
    def generate_dependency_map_report(self) -> str:
        """Generate dependency mapping report"""
        context = self.context_manager.context
        
        file_deps = context.file_dependencies
        imports = context.discovered_imports
        cross_refs = context.cross_references
        
        if not file_deps and not imports:
            return self._generate_empty_report("Dependency Map", "No dependencies discovered in the codebase.")
        
        report = f"""# 🗺️ Dependency Map Report

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for session {self.session_id}*

## 📊 Dependency Overview
- **File Dependencies**: {len(file_deps)}
- **Import Statements**: {len(imports)}
- **Cross-References**: {len(cross_refs)}

"""
        
        # External vs Internal dependencies
        external_imports = []
        internal_imports = []
        
        for imp in imports:
            module = imp.get('module', '')
            if any(prefix in module for prefix in ['/', './', '../']):
                internal_imports.append(imp)
            else:
                external_imports.append(imp)
        
        # External dependencies
        if external_imports:
            report += f"## 🌐 External Dependencies ({len(external_imports)})\n\n"
            
            # Group by module
            external_modules = {}
            for imp in external_imports:
                module = imp.get('module', 'Unknown')
                source = imp.get('source_file', 'Unknown')
                
                if module not in external_modules:
                    external_modules[module] = set()
                external_modules[module].add(source)
            
            # Sort by usage count
            sorted_modules = sorted(external_modules.items(), key=lambda x: len(x[1]), reverse=True)
            
            for module, files in sorted_modules:
                report += f"### `{module}` (used in {len(files)} files)\n\n"
                for file_path in sorted(files)[:5]:  # Show first 5 files
                    report += f"- `{file_path}`\n"
                if len(files) > 5:
                    report += f"- ... and {len(files) - 5} more files\n"
                report += "\n"
        
        # Internal dependencies
        if internal_imports:
            report += f"## 🏠 Internal Dependencies ({len(internal_imports)})\n\n"
            
            # Analyze internal module structure
            internal_modules = {}
            for imp in internal_imports:
                module = imp.get('module', 'Unknown')
                source = imp.get('source_file', 'Unknown')
                
                if module not in internal_modules:
                    internal_modules[module] = set()
                internal_modules[module].add(source)
            
            for module, files in sorted(internal_modules.items()):
                report += f"- `{module}` ← imported by {len(files)} files\n"
            
            report += "\n"
        
        # Dependency graph analysis
        if file_deps:
            report += f"## 📈 Dependency Graph Analysis\n\n"
            
            # Calculate dependency metrics
            total_files = len(file_deps)
            total_dependencies = sum(len(deps) for deps in file_deps.values())
            avg_dependencies = total_dependencies / total_files if total_files > 0 else 0
            
            report += f"- **Total files with dependencies**: {total_files}\n"
            report += f"- **Total dependency relationships**: {total_dependencies}\n"
            report += f"- **Average dependencies per file**: {avg_dependencies:.1f}\n\n"
            
            # Find cycles (simple detection)
            cycles = self._detect_simple_cycles(file_deps)
            if cycles:
                report += f"### ⚠️ Potential Circular Dependencies ({len(cycles)})\n\n"
                for cycle in cycles[:5]:  # Show first 5 cycles
                    report += f"- {' → '.join(cycle)} → {cycle[0]}\n"
                if len(cycles) > 5:
                    report += f"- ... and {len(cycles) - 5} more cycles\n"
                report += "\n"
            
            # Most dependent files
            most_dependent = sorted(file_deps.items(), key=lambda x: len(x[1]), reverse=True)[:10]
            if most_dependent:
                report += f"### 📊 Most Dependent Files\n\n"
                for file_path, deps in most_dependent:
                    report += f"- `{file_path}`: {len(deps)} dependencies\n"
                report += "\n"
        
        return report
    
    def _generate_empty_report(self, report_title: str, message: str) -> str:
        """Generate an empty report with a message"""
        return f"""# {report_title}

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for session {self.session_id}*

## ℹ️ Information

{message}

This could be because:
- The analysis is still in progress
- No relevant code patterns were detected
- The codebase doesn't contain this type of information
- Additional file processing is needed

Use the batch processor to continue analysis or try different analysis goals.
"""
    
    def _mask_connection_string(self, connection_string: str) -> str:
        """Mask sensitive information in connection strings"""
        # Simple masking for common patterns
        masked = connection_string
        
        # Mask passwords
        import re
        masked = re.sub(r'password=([^;]+)', 'password=***', masked, flags=re.IGNORECASE)
        masked = re.sub(r'pwd=([^;]+)', 'pwd=***', masked, flags=re.IGNORECASE)
        
        # Mask API keys
        masked = re.sub(r'key=([^;]+)', 'key=***', masked, flags=re.IGNORECASE)
        masked = re.sub(r'token=([^;]+)', 'token=***', masked, flags=re.IGNORECASE)
        
        return masked
    
    def _analyze_coupling(self, file_deps: Dict[str, List[str]]) -> str:
        """Analyze coupling between modules"""
        if not file_deps:
            return ""
        
        # Calculate coupling metrics
        coupling_scores = {}
        for file_path, deps in file_deps.items():
            coupling_scores[file_path] = len(deps)
        
        # Classify coupling levels
        high_coupling = [f for f, score in coupling_scores.items() if score > 10]
        medium_coupling = [f for f, score in coupling_scores.items() if 5 <= score <= 10]
        low_coupling = [f for f, score in coupling_scores.items() if score < 5]
        
        analysis = ""
        if high_coupling:
            analysis += f"**High Coupling** ({len(high_coupling)} files): Consider refactoring\n"
            for file_path in high_coupling[:3]:
                analysis += f"- `{file_path}` ({coupling_scores[file_path]} dependencies)\n"
        
        if medium_coupling:
            analysis += f"**Medium Coupling** ({len(medium_coupling)} files): Monitor complexity\n"
        
        if low_coupling:
            analysis += f"**Low Coupling** ({len(low_coupling)} files): Good modularity\n"
        
        return analysis
    
    def _detect_simple_cycles(self, file_deps: Dict[str, List[str]]) -> List[List[str]]:
        """Simple cycle detection in dependency graph"""
        cycles = []
        visited = set()
        
        def dfs(node: str, path: List[str], current_visited: Set[str]):
            if node in current_visited:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            current_visited.add(node)
            path.append(node)
            
            for dep in file_deps.get(node, []):
                if dep in file_deps:  # Only follow internal dependencies
                    dfs(dep, path.copy(), current_visited.copy())
            
            visited.add(node)
        
        for file_path in file_deps:
            if file_path not in visited:
                dfs(file_path, [], set())
        
        return cycles[:10]  # Return first 10 cycles


# Function tools for external access
@function_tool
async def generate_report(
    session_id: str,
    report_type: str,
    output_file: Optional[str] = None
) -> str:
    """
    Generate a structured analysis report from session context.
    
    Args:
        session_id: ID of the processing session
        report_type: Type of report - "api_inventory", "data_flow", "architecture_overview", 
                    "database_schema", "security_analysis", "dependency_map"
        output_file: Optional file path to save the report
    
    Returns:
        Generated report content
    """
    try:
        # Validate report type
        try:
            template = ReportTemplate(report_type.lower())
        except ValueError:
            available_types = [t.value for t in ReportTemplate]
            return f"❌ Invalid report type: {report_type}\nAvailable types: {', '.join(available_types)}"
        
        # Create report generator
        generator = ReportGenerator(session_id)
        
        # Generate report based on type
        if template == ReportTemplate.API_INVENTORY:
            report_content = generator.generate_api_inventory_report()
        elif template == ReportTemplate.DATA_FLOW:
            report_content = generator.generate_data_flow_report()
        elif template == ReportTemplate.ARCHITECTURE_OVERVIEW:
            report_content = generator.generate_architecture_overview_report()
        elif template == ReportTemplate.DATABASE_SCHEMA:
            report_content = generator.generate_database_schema_report()
        elif template == ReportTemplate.SECURITY_ANALYSIS:
            report_content = generator.generate_security_analysis_report()
        elif template == ReportTemplate.DEPENDENCY_MAP:
            report_content = generator.generate_dependency_map_report()
        else:
            return f"❌ Report type not implemented: {report_type}"
        
        # Save to file if requested
        if output_file:
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                file_size = len(report_content.encode('utf-8'))
                return f"""✅ **Report Generated Successfully**

- **Report Type**: {report_type}
- **Session**: {session_id}
- **Output File**: `{output_file}`
- **File Size**: {file_size:,} bytes ({file_size / 1024:.1f} KB)

## 📄 Report Preview (first 1000 characters):

{report_content[:1000]}{'...' if len(report_content) > 1000 else ''}

The complete report has been saved to the specified file.
"""
            
            except Exception as e:
                return f"✅ Report generated but failed to save to file: {str(e)}\n\n{report_content}"
        
        return report_content
        
    except Exception as e:
        return f"❌ Error generating report: {str(e)}"


@function_tool
async def list_available_report_types() -> str:
    """
    List all available report types with descriptions.
    
    Returns:
        List of available report types and their descriptions
    """
    report_descriptions = {
        ReportTemplate.API_INVENTORY: "Comprehensive listing of all discovered API endpoints, organized by method and file",
        ReportTemplate.DATA_FLOW: "Analysis of data flow patterns, database connections, and processing functions",
        ReportTemplate.ARCHITECTURE_OVERVIEW: "High-level system architecture analysis including patterns and frameworks",
        ReportTemplate.DATABASE_SCHEMA: "Database connections, schema information, and related functions",
        ReportTemplate.SECURITY_ANALYSIS: "Security-related functions, authentication endpoints, and recommendations",
        ReportTemplate.DEPENDENCY_MAP: "Dependency relationships, coupling analysis, and potential circular dependencies"
    }
    
    output = """# 📊 Available Report Types

Choose from the following report templates for your analysis:

"""
    
    for template, description in report_descriptions.items():
        output += f"## {template.value.replace('_', ' ').title()}\n"
        output += f"**Type**: `{template.value}`\n\n"
        output += f"{description}\n\n"
        output += "---\n\n"
    
    output += """## Usage

Use `generate_report(session_id, report_type, output_file)` to generate any of these reports.

Example:
```
generate_report("abc123", "api_inventory", "./reports/api_report.md")
```
"""
    
    return output