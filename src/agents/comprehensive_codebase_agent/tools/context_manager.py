import json
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict
from agents import function_tool


@dataclass
class AnalysisContext:
    """Context information passed between batches"""
    # Discovered code elements
    discovered_apis: List[Dict[str, Any]] = field(default_factory=list)
    discovered_functions: List[Dict[str, Any]] = field(default_factory=list)
    discovered_classes: List[Dict[str, Any]] = field(default_factory=list)
    discovered_imports: List[Dict[str, Any]] = field(default_factory=list)
    discovered_databases: List[Dict[str, Any]] = field(default_factory=list)
    
    # Relationships and dependencies
    file_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    module_relationships: Dict[str, List[str]] = field(default_factory=dict)
    api_to_implementation: Dict[str, str] = field(default_factory=dict)
    
    # Patterns and architectures
    detected_patterns: Set[str] = field(default_factory=set)
    framework_usage: Dict[str, List[str]] = field(default_factory=dict)
    common_configurations: Dict[str, Any] = field(default_factory=dict)
    
    # Processing metadata
    processed_files: Set[str] = field(default_factory=set)
    file_analysis_cache: Dict[str, str] = field(default_factory=dict)  # file_path -> analysis_summary
    cross_references: Dict[str, List[str]] = field(default_factory=dict)
    
    # Analysis-specific contexts
    security_findings: List[Dict[str, Any]] = field(default_factory=list)
    performance_notes: List[Dict[str, Any]] = field(default_factory=list)
    code_quality_issues: List[Dict[str, Any]] = field(default_factory=list)
    
    # Session metadata
    session_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


class ContextManager:
    """Manages context passing between batches to avoid duplication"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.context = AnalysisContext(session_id=session_id)
        self._deduplication_hashes: Set[str] = set()
    
    def add_discovered_apis(self, apis: List[Dict[str, Any]], source_file: str) -> int:
        """Add discovered API endpoints, avoiding duplicates"""
        added_count = 0
        
        for api in apis:
            # Create a hash for deduplication
            api_key = f"{api.get('method', 'GET')}:{api.get('path', '')}"
            api_hash = hashlib.md5(api_key.encode()).hexdigest()
            
            if api_hash not in self._deduplication_hashes:
                # Add source file information
                api_with_source = {**api, "source_file": source_file, "discovered_at": datetime.now().isoformat()}
                self.context.discovered_apis.append(api_with_source)
                self._deduplication_hashes.add(api_hash)
                added_count += 1
        
        self._update_timestamp()
        return added_count
    
    def add_discovered_functions(self, functions: List[Dict[str, Any]], source_file: str) -> int:
        """Add discovered functions, avoiding duplicates"""
        added_count = 0
        
        for func in functions:
            # Create unique identifier for function
            func_key = f"{source_file}:{func.get('name', '')}:{func.get('line_number', 0)}"
            func_hash = hashlib.md5(func_key.encode()).hexdigest()
            
            if func_hash not in self._deduplication_hashes:
                func_with_source = {**func, "source_file": source_file, "discovered_at": datetime.now().isoformat()}
                self.context.discovered_functions.append(func_with_source)
                self._deduplication_hashes.add(func_hash)
                added_count += 1
        
        self._update_timestamp()
        return added_count
    
    def add_discovered_classes(self, classes: List[Dict[str, Any]], source_file: str) -> int:
        """Add discovered classes, avoiding duplicates"""
        added_count = 0
        
        for cls in classes:
            cls_key = f"{source_file}:{cls.get('name', '')}:{cls.get('line_number', 0)}"
            cls_hash = hashlib.md5(cls_key.encode()).hexdigest()
            
            if cls_hash not in self._deduplication_hashes:
                cls_with_source = {**cls, "source_file": source_file, "discovered_at": datetime.now().isoformat()}
                self.context.discovered_classes.append(cls_with_source)
                self._deduplication_hashes.add(cls_hash)
                added_count += 1
        
        self._update_timestamp()
        return added_count
    
    def add_discovered_imports(self, imports: List[Dict[str, Any]], source_file: str) -> int:
        """Add discovered imports and track dependencies"""
        added_count = 0
        
        for imp in imports:
            import_key = f"{source_file}:{imp.get('module', '')}:{imp.get('name', '')}"
            import_hash = hashlib.md5(import_key.encode()).hexdigest()
            
            if import_hash not in self._deduplication_hashes:
                imp_with_source = {**imp, "source_file": source_file, "discovered_at": datetime.now().isoformat()}
                self.context.discovered_imports.append(imp_with_source)
                self._deduplication_hashes.add(import_hash)
                added_count += 1
                
                # Track file dependencies
                imported_module = imp.get('module', '')
                if imported_module:
                    if source_file not in self.context.file_dependencies:
                        self.context.file_dependencies[source_file] = []
                    if imported_module not in self.context.file_dependencies[source_file]:
                        self.context.file_dependencies[source_file].append(imported_module)
        
        self._update_timestamp()
        return added_count
    
    def add_discovered_databases(self, databases: List[Dict[str, Any]], source_file: str) -> int:
        """Add discovered database connections and queries"""
        added_count = 0
        
        for db in databases:
            db_key = f"{source_file}:{db.get('type', '')}:{db.get('connection_string', '')}"
            db_hash = hashlib.md5(db_key.encode()).hexdigest()
            
            if db_hash not in self._deduplication_hashes:
                db_with_source = {**db, "source_file": source_file, "discovered_at": datetime.now().isoformat()}
                self.context.discovered_databases.append(db_with_source)
                self._deduplication_hashes.add(db_hash)
                added_count += 1
        
        self._update_timestamp()
        return added_count
    
    def add_framework_usage(self, framework: str, usage_details: List[str], source_file: str):
        """Track framework usage across files"""
        if framework not in self.context.framework_usage:
            self.context.framework_usage[framework] = []
        
        for detail in usage_details:
            usage_entry = f"{source_file}: {detail}"
            if usage_entry not in self.context.framework_usage[framework]:
                self.context.framework_usage[framework].append(usage_entry)
        
        self._update_timestamp()
    
    def add_detected_pattern(self, pattern: str, source_file: str):
        """Add detected architectural or design pattern"""
        pattern_with_source = f"{pattern} (found in {source_file})"
        self.context.detected_patterns.add(pattern_with_source)
        self._update_timestamp()
    
    def add_cross_reference(self, from_file: str, to_file: str, relationship_type: str):
        """Add cross-reference between files"""
        if from_file not in self.context.cross_references:
            self.context.cross_references[from_file] = []
        
        reference = f"{to_file} ({relationship_type})"
        if reference not in self.context.cross_references[from_file]:
            self.context.cross_references[from_file].append(reference)
        
        self._update_timestamp()
    
    def mark_file_processed(self, file_path: str, analysis_summary: str):
        """Mark a file as processed and cache its analysis summary"""
        self.context.processed_files.add(file_path)
        self.context.file_analysis_cache[file_path] = analysis_summary
        self._update_timestamp()
    
    def is_file_processed(self, file_path: str) -> bool:
        """Check if a file has already been processed"""
        return file_path in self.context.processed_files
    
    def get_file_analysis_summary(self, file_path: str) -> Optional[str]:
        """Get cached analysis summary for a file"""
        return self.context.file_analysis_cache.get(file_path)
    
    def get_related_files(self, file_path: str) -> List[str]:
        """Get files that are related to the given file"""
        related = []
        
        # Files that import from this file
        for file, deps in self.context.file_dependencies.items():
            if any(file_path in dep for dep in deps):
                related.append(file)
        
        # Files that this file imports from
        if file_path in self.context.file_dependencies:
            related.extend(self.context.file_dependencies[file_path])
        
        # Cross-referenced files
        if file_path in self.context.cross_references:
            related.extend([ref.split(' (')[0] for ref in self.context.cross_references[file_path]])
        
        return list(set(related))  # Remove duplicates
    
    def get_analysis_context_for_file(self, file_path: str) -> Dict[str, Any]:
        """Get relevant context information for analyzing a specific file"""
        related_files = self.get_related_files(file_path)
        
        # Get relevant APIs that might be related to this file
        relevant_apis = [
            api for api in self.context.discovered_apis
            if api.get('source_file') in related_files or file_path in api.get('source_file', '')
        ]
        
        # Get relevant functions and classes
        relevant_functions = [
            func for func in self.context.discovered_functions
            if func.get('source_file') in related_files
        ]
        
        relevant_classes = [
            cls for cls in self.context.discovered_classes
            if cls.get('source_file') in related_files
        ]
        
        return {
            "related_files": related_files,
            "relevant_apis": relevant_apis,
            "relevant_functions": relevant_functions,
            "relevant_classes": relevant_classes,
            "known_patterns": list(self.context.detected_patterns),
            "framework_usage": dict(self.context.framework_usage),
            "file_already_processed": self.is_file_processed(file_path)
        }
    
    def get_comprehensive_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of all discovered information"""
        return {
            "session_info": {
                "session_id": self.session_id,
                "created_at": self.context.created_at.isoformat(),
                "last_updated": self.context.last_updated.isoformat(),
                "processed_files_count": len(self.context.processed_files)
            },
            "discovered_elements": {
                "apis": len(self.context.discovered_apis),
                "functions": len(self.context.discovered_functions),
                "classes": len(self.context.discovered_classes),
                "imports": len(self.context.discovered_imports),
                "databases": len(self.context.discovered_databases)
            },
            "architecture_insights": {
                "detected_patterns": list(self.context.detected_patterns),
                "frameworks": list(self.context.framework_usage.keys()),
                "file_dependency_count": len(self.context.file_dependencies),
                "cross_reference_count": len(self.context.cross_references)
            },
            "top_apis": self.context.discovered_apis[:10],  # Top 10 APIs
            "top_frameworks": {
                framework: len(usages) 
                for framework, usages in self.context.framework_usage.items()
            }
        }
    
    def export_context(self) -> str:
        """Export context to JSON string"""
        # Convert context to serializable format
        exportable_context = {
            "discovered_apis": self.context.discovered_apis,
            "discovered_functions": self.context.discovered_functions,
            "discovered_classes": self.context.discovered_classes,
            "discovered_imports": self.context.discovered_imports,
            "discovered_databases": self.context.discovered_databases,
            "file_dependencies": self.context.file_dependencies,
            "module_relationships": self.context.module_relationships,
            "api_to_implementation": self.context.api_to_implementation,
            "detected_patterns": list(self.context.detected_patterns),
            "framework_usage": self.context.framework_usage,
            "common_configurations": self.context.common_configurations,
            "processed_files": list(self.context.processed_files),
            "file_analysis_cache": self.context.file_analysis_cache,
            "cross_references": self.context.cross_references,
            "session_id": self.context.session_id,
            "created_at": self.context.created_at.isoformat(),
            "last_updated": self.context.last_updated.isoformat()
        }
        
        return json.dumps(exportable_context, indent=2, ensure_ascii=False)
    
    def import_context(self, context_json: str):
        """Import context from JSON string"""
        data = json.loads(context_json)
        
        self.context.discovered_apis = data.get("discovered_apis", [])
        self.context.discovered_functions = data.get("discovered_functions", [])
        self.context.discovered_classes = data.get("discovered_classes", [])
        self.context.discovered_imports = data.get("discovered_imports", [])
        self.context.discovered_databases = data.get("discovered_databases", [])
        self.context.file_dependencies = data.get("file_dependencies", {})
        self.context.module_relationships = data.get("module_relationships", {})
        self.context.api_to_implementation = data.get("api_to_implementation", {})
        self.context.detected_patterns = set(data.get("detected_patterns", []))
        self.context.framework_usage = data.get("framework_usage", {})
        self.context.common_configurations = data.get("common_configurations", {})
        self.context.processed_files = set(data.get("processed_files", []))
        self.context.file_analysis_cache = data.get("file_analysis_cache", {})
        self.context.cross_references = data.get("cross_references", {})
        
        # Rebuild deduplication hashes
        self._rebuild_deduplication_hashes()
        self._update_timestamp()
    
    def _rebuild_deduplication_hashes(self):
        """Rebuild deduplication hashes from current context"""
        self._deduplication_hashes.clear()
        
        # Rebuild API hashes
        for api in self.context.discovered_apis:
            api_key = f"{api.get('method', 'GET')}:{api.get('path', '')}"
            self._deduplication_hashes.add(hashlib.md5(api_key.encode()).hexdigest())
        
        # Rebuild function hashes
        for func in self.context.discovered_functions:
            func_key = f"{func.get('source_file', '')}:{func.get('name', '')}:{func.get('line_number', 0)}"
            self._deduplication_hashes.add(hashlib.md5(func_key.encode()).hexdigest())
        
        # Rebuild class hashes
        for cls in self.context.discovered_classes:
            cls_key = f"{cls.get('source_file', '')}:{cls.get('name', '')}:{cls.get('line_number', 0)}"
            self._deduplication_hashes.add(hashlib.md5(cls_key.encode()).hexdigest())
        
        # Rebuild import hashes
        for imp in self.context.discovered_imports:
            import_key = f"{imp.get('source_file', '')}:{imp.get('module', '')}:{imp.get('name', '')}"
            self._deduplication_hashes.add(hashlib.md5(import_key.encode()).hexdigest())
    
    def _update_timestamp(self):
        """Update the last modified timestamp"""
        self.context.last_updated = datetime.now()


# Global context managers by session
_context_managers: Dict[str, ContextManager] = {}


def get_context_manager(session_id: str) -> ContextManager:
    """Get or create a context manager for a session"""
    if session_id not in _context_managers:
        _context_managers[session_id] = ContextManager(session_id)
    return _context_managers[session_id]


# Function tools for external access
@function_tool
async def add_analysis_findings(
    session_id: str,
    file_path: str,
    finding_type: str,
    findings_data: str
) -> str:
    """
    Add analysis findings to the session context.
    
    Args:
        session_id: ID of the processing session
        file_path: Path of the file being analyzed
        finding_type: Type of findings - "apis", "functions", "classes", "imports", "databases"
        findings_data: JSON string containing the findings
    
    Returns:
        Summary of added findings
    """
    try:
        context_manager = get_context_manager(session_id)
        
        # Parse findings data
        try:
            findings = json.loads(findings_data)
            if not isinstance(findings, list):
                findings = [findings]
        except json.JSONDecodeError:
            return f"❌ Error: Invalid JSON in findings_data"
        
        # Add findings based on type
        added_count = 0
        if finding_type.lower() == "apis":
            added_count = context_manager.add_discovered_apis(findings, file_path)
        elif finding_type.lower() == "functions":
            added_count = context_manager.add_discovered_functions(findings, file_path)
        elif finding_type.lower() == "classes":
            added_count = context_manager.add_discovered_classes(findings, file_path)
        elif finding_type.lower() == "imports":
            added_count = context_manager.add_discovered_imports(findings, file_path)
        elif finding_type.lower() == "databases":
            added_count = context_manager.add_discovered_databases(findings, file_path)
        else:
            return f"❌ Error: Unknown finding type '{finding_type}'. Use: apis, functions, classes, imports, databases"
        
        return f"""✅ **Analysis Findings Added**

- **Session**: {session_id}
- **File**: {file_path}
- **Type**: {finding_type}
- **Added**: {added_count} new items
- **Duplicates Skipped**: {len(findings) - added_count}

## 📊 Updated Context Summary
{_format_context_summary(context_manager.get_comprehensive_summary())}
"""
        
    except Exception as e:
        return f"❌ Error adding analysis findings: {str(e)}"


@function_tool
async def get_file_context(session_id: str, file_path: str) -> str:
    """
    Get relevant context information for analyzing a specific file.
    
    Args:
        session_id: ID of the processing session
        file_path: Path of the file to get context for
    
    Returns:
        Relevant context information for the file
    """
    try:
        context_manager = get_context_manager(session_id)
        context_info = context_manager.get_analysis_context_for_file(file_path)
        
        output = f"""# 🧠 Analysis Context for: {file_path}

## 🔗 Related Files ({len(context_info['related_files'])})
"""
        for related_file in context_info['related_files'][:10]:  # Show top 10
            output += f"- `{related_file}`\n"
        
        if len(context_info['related_files']) > 10:
            output += f"- ... and {len(context_info['related_files']) - 10} more\n"
        
        output += f"""
## 🚀 Relevant APIs ({len(context_info['relevant_apis'])})
"""
        for api in context_info['relevant_apis'][:5]:  # Show top 5
            method = api.get('method', 'GET')
            path = api.get('path', 'unknown')
            source = api.get('source_file', 'unknown')
            output += f"- **{method}** `{path}` (from {source})\n"
        
        output += f"""
## 🔧 Relevant Functions ({len(context_info['relevant_functions'])})
"""
        for func in context_info['relevant_functions'][:5]:  # Show top 5
            name = func.get('name', 'unknown')
            source = func.get('source_file', 'unknown')
            output += f"- `{name}()` (from {source})\n"
        
        output += f"""
## 🏗️ Detected Patterns
"""
        for pattern in list(context_info['known_patterns'])[:5]:
            output += f"- {pattern}\n"
        
        output += f"""
## 📚 Framework Usage
"""
        for framework, usages in context_info['framework_usage'].items():
            output += f"- **{framework}**: {len(usages)} usages\n"
        
        output += f"""
## ℹ️ Processing Status
- **File already processed**: {"Yes" if context_info['file_already_processed'] else "No"}
"""
        
        if context_info['file_already_processed']:
            summary = context_manager.get_file_analysis_summary(file_path)
            if summary:
                output += f"- **Previous analysis**: {summary[:200]}...\n"
        
        return output
        
    except Exception as e:
        return f"❌ Error getting file context: {str(e)}"


@function_tool
async def mark_file_processed(
    session_id: str,
    file_path: str,
    analysis_summary: str
) -> str:
    """
    Mark a file as processed and save its analysis summary.
    
    Args:
        session_id: ID of the processing session
        file_path: Path of the processed file
        analysis_summary: Brief summary of the analysis results
    
    Returns:
        Confirmation message
    """
    try:
        context_manager = get_context_manager(session_id)
        context_manager.mark_file_processed(file_path, analysis_summary)
        
        total_processed = len(context_manager.context.processed_files)
        
        return f"""✅ **File Marked as Processed**

- **Session**: {session_id}
- **File**: {file_path}
- **Analysis Summary**: {analysis_summary[:100]}...
- **Total Processed Files**: {total_processed}

The file context has been cached and will be available for cross-referencing during analysis of related files.
"""
        
    except Exception as e:
        return f"❌ Error marking file as processed: {str(e)}"


@function_tool
async def get_session_context_summary(session_id: str) -> str:
    """
    Get a comprehensive summary of all discoveries in the session.
    
    Args:
        session_id: ID of the processing session
    
    Returns:
        Comprehensive context summary
    """
    try:
        context_manager = get_context_manager(session_id)
        summary = context_manager.get_comprehensive_summary()
        
        return f"""# 🧠 Session Context Summary

## 📊 Session Information
- **Session ID**: {summary['session_info']['session_id']}
- **Created**: {summary['session_info']['created_at']}
- **Last Updated**: {summary['session_info']['last_updated']}
- **Processed Files**: {summary['session_info']['processed_files_count']}

## 🔍 Discovered Elements
- **APIs**: {summary['discovered_elements']['apis']}
- **Functions**: {summary['discovered_elements']['functions']}
- **Classes**: {summary['discovered_elements']['classes']}
- **Imports**: {summary['discovered_elements']['imports']}
- **Databases**: {summary['discovered_elements']['databases']}

## 🏗️ Architecture Insights
- **Patterns Detected**: {len(summary['architecture_insights']['detected_patterns'])}
- **Frameworks Used**: {len(summary['architecture_insights']['frameworks'])}
- **File Dependencies**: {summary['architecture_insights']['file_dependency_count']}
- **Cross References**: {summary['architecture_insights']['cross_reference_count']}

### Detected Patterns:
{chr(10).join(f"- {pattern}" for pattern in summary['architecture_insights']['detected_patterns'][:10])}

### Framework Usage:
{chr(10).join(f"- **{fw}**: {count} usages" for fw, count in summary['top_frameworks'].items())}

## 🚀 Top Discovered APIs
{chr(10).join(f"- **{api.get('method', 'GET')}** `{api.get('path', 'unknown')}` ({api.get('source_file', 'unknown')})" for api in summary['top_apis'][:10])}

This context is continuously updated as more files are processed and will help avoid duplicate analysis and maintain consistency across batches.
"""
        
    except Exception as e:
        return f"❌ Error getting session context summary: {str(e)}"


def _format_context_summary(summary: Dict[str, Any]) -> str:
    """Helper function to format context summary"""
    elements = summary['discovered_elements']
    return f"""- **Total APIs**: {elements['apis']}
- **Total Functions**: {elements['functions']}
- **Total Classes**: {elements['classes']}
- **Total Imports**: {elements['imports']}
- **Frameworks**: {len(summary['architecture_insights']['frameworks'])}
- **Patterns**: {len(summary['architecture_insights']['detected_patterns'])}"""