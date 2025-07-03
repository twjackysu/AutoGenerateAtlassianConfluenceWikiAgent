"""
Documentation Generation Agent - Responsible for generating structured wiki content
"""
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
from agents import Agent, Tool
from src.models.claude_model import ClaudeModel
from src.config import config

class DocumentationGenerationAgent:
    """Agent responsible for generating structured documentation"""
    
    def __init__(self):
        self.agent = Agent(
            name="Documentation Generation Agent",
            instructions="""
            You are a technical documentation specialist. Your responsibilities include:
            1. Generate comprehensive wiki documentation from code analysis
            2. Create structured Markdown content for Confluence
            3. Organize content based on user requirements and preferences
            4. Generate different types of documentation (architecture, API, user guides)
            5. Ensure documentation is clear, accurate, and well-formatted
            6. Include code examples, diagrams descriptions, and best practices
            
            Create documentation that is useful for developers, architects, and stakeholders.
            Focus on clarity, completeness, and maintainability.
            """,
            model=ClaudeModel(),
            tools=[
                Tool(
                    name="generate_architecture_doc",
                    description="Generate architecture documentation",
                    function=self.generate_architecture_doc
                ),
                Tool(
                    name="generate_api_documentation",
                    description="Generate API documentation",
                    function=self.generate_api_documentation
                ),
                Tool(
                    name="generate_component_docs",
                    description="Generate component-level documentation",
                    function=self.generate_component_docs
                ),
                Tool(
                    name="generate_setup_guide",
                    description="Generate setup and installation guide",
                    function=self.generate_setup_guide
                ),
                Tool(
                    name="generate_data_flow_docs",
                    description="Generate data flow documentation",
                    function=self.generate_data_flow_docs
                ),
                Tool(
                    name="create_overview_doc",
                    description="Create project overview documentation",
                    function=self.create_overview_doc
                )
            ]
        )
    
    async def generate_architecture_doc(self, analysis_data: Dict[str, Any], user_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate architecture documentation"""
        try:
            project_structure = analysis_data.get("structure", {})
            dependencies = analysis_data.get("dependencies", {})
            
            # Build architecture documentation
            doc_content = f"""# Architecture Documentation
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Project Overview
- **Project Type**: {project_structure.get('project_type', 'Unknown')}
- **Primary Languages**: {', '.join(project_structure.get('languages', {}).keys())}
- **Entry Points**: {', '.join(project_structure.get('entry_points', []))}

## System Architecture

### High-Level Architecture
{self._generate_architecture_description(project_structure)}

### Component Structure
{self._generate_component_structure(project_structure)}

### Dependencies
{self._generate_dependencies_section(dependencies)}

### Data Flow
{self._generate_data_flow_section(analysis_data.get('data_flows', {}))}

## Design Patterns and Decisions
{self._analyze_design_patterns(analysis_data)}

## Scalability Considerations
{self._generate_scalability_notes(project_structure)}
"""
            
            return {
                "status": "success",
                "document": {
                    "title": "Architecture Documentation",
                    "content": doc_content,
                    "type": "architecture",
                    "sections": ["overview", "architecture", "components", "dependencies", "data_flow"]
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate architecture documentation: {str(e)}"
            }
    
    async def generate_api_documentation(self, analysis_data: Dict[str, Any], user_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API documentation"""
        try:
            endpoints = analysis_data.get("api_endpoints", [])
            
            doc_content = f"""# API Documentation
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## API Overview
This document describes the API endpoints and their usage.

### Available Endpoints
{self._generate_endpoints_table(endpoints)}

## Endpoint Details
{self._generate_endpoint_details(endpoints)}

## Authentication
{self._generate_auth_section(analysis_data)}

## Rate Limiting
{self._generate_rate_limiting_section()}

## Error Handling
{self._generate_error_handling_section()}

## Code Examples
{self._generate_api_examples(endpoints)}
"""
            
            return {
                "status": "success",
                "document": {
                    "title": "API Documentation",
                    "content": doc_content,
                    "type": "api",
                    "sections": ["overview", "endpoints", "authentication", "examples"]
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate API documentation: {str(e)}"
            }
    
    async def generate_component_docs(self, analysis_data: Dict[str, Any], user_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate component-level documentation"""
        try:
            files_analysis = analysis_data.get("files_analysis", [])
            
            doc_content = f"""# Component Documentation
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Components Overview
{self._generate_components_overview(files_analysis)}

## Component Details
{self._generate_component_details(files_analysis)}

## Component Relationships
{self._generate_component_relationships(files_analysis)}

## Testing Guidelines
{self._generate_testing_guidelines(analysis_data)}
"""
            
            return {
                "status": "success",
                "document": {
                    "title": "Component Documentation",
                    "content": doc_content,
                    "type": "components",
                    "sections": ["overview", "details", "relationships", "testing"]
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate component documentation: {str(e)}"
            }
    
    async def generate_setup_guide(self, analysis_data: Dict[str, Any], user_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate setup and installation guide"""
        try:
            dependencies = analysis_data.get("dependencies", {})
            project_structure = analysis_data.get("structure", {})
            
            doc_content = f"""# Setup and Installation Guide
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Prerequisites
{self._generate_prerequisites(dependencies, project_structure)}

## Installation Steps
{self._generate_installation_steps(dependencies, project_structure)}

## Configuration
{self._generate_configuration_section(analysis_data)}

## Environment Setup
{self._generate_environment_setup(project_structure)}

## Verification
{self._generate_verification_steps(project_structure)}

## Troubleshooting
{self._generate_troubleshooting_section()}
"""
            
            return {
                "status": "success",
                "document": {
                    "title": "Setup and Installation Guide",
                    "content": doc_content,
                    "type": "setup",
                    "sections": ["prerequisites", "installation", "configuration", "verification"]
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate setup guide: {str(e)}"
            }
    
    async def generate_data_flow_docs(self, analysis_data: Dict[str, Any], user_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data flow documentation"""
        try:
            data_flows = analysis_data.get("data_flows", {})
            
            doc_content = f"""# Data Flow Documentation
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Data Flow Overview
{self._generate_data_flow_overview(data_flows)}

## Database Operations
{self._generate_database_operations(data_flows.get('database_connections', []))}

## External API Interactions
{self._generate_api_interactions(data_flows.get('api_calls', []))}

## File Operations
{self._generate_file_operations(data_flows.get('file_operations', []))}

## Data Transformations
{self._generate_data_transformations(data_flows.get('data_transformations', []))}

## Security Considerations
{self._generate_security_considerations()}
"""
            
            return {
                "status": "success",
                "document": {
                    "title": "Data Flow Documentation",
                    "content": doc_content,
                    "type": "data_flow",
                    "sections": ["overview", "database", "apis", "files", "security"]
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate data flow documentation: {str(e)}"
            }
    
    async def create_overview_doc(self, analysis_data: Dict[str, Any], user_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create project overview documentation"""
        try:
            project_structure = analysis_data.get("structure", {})
            dependencies = analysis_data.get("dependencies", {})
            
            doc_content = f"""# Project Overview
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Project Summary
{self._generate_project_summary(project_structure, dependencies)}

## Key Features
{self._generate_key_features(analysis_data)}

## Technology Stack
{self._generate_technology_stack(dependencies, project_structure)}

## Project Structure
{self._generate_project_structure_overview(project_structure)}

## Getting Started
{self._generate_getting_started(project_structure)}

## Documentation Index
{self._generate_documentation_index()}
"""
            
            return {
                "status": "success",
                "document": {
                    "title": "Project Overview",
                    "content": doc_content,
                    "type": "overview",
                    "sections": ["summary", "features", "tech_stack", "structure", "getting_started"]
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to create overview documentation: {str(e)}"
            }
    
    # Helper methods for generating documentation sections
    def _generate_architecture_description(self, structure: Dict) -> str:
        project_type = structure.get("project_type", "unknown")
        if project_type == "python":
            return "This is a Python-based application with a modular architecture."
        elif project_type == "node.js":
            return "This is a Node.js application following modern JavaScript/TypeScript patterns."
        else:
            return "This application follows a multi-language architecture."
    
    def _generate_component_structure(self, structure: Dict) -> str:
        languages = structure.get("languages", {})
        content = "### File Distribution\n"
        for ext, count in languages.items():
            content += f"- {ext}: {count} files\n"
        return content
    
    def _generate_dependencies_section(self, dependencies: Dict) -> str:
        content = "### External Dependencies\n"
        for lang, deps in dependencies.items():
            if isinstance(deps, dict):
                for dep_type, dep_list in deps.items():
                    if dep_list:
                        content += f"#### {lang.title()} {dep_type.replace('_', ' ').title()}\n"
                        for dep in dep_list[:10]:  # Limit to first 10
                            content += f"- {dep}\n"
        return content
    
    def _generate_data_flow_section(self, data_flows: Dict) -> str:
        content = "### Data Flow Patterns\n"
        for flow_type, flows in data_flows.items():
            if flows:
                content += f"- **{flow_type.replace('_', ' ').title()}**: {len(flows)} occurrences\n"
        return content
    
    def _analyze_design_patterns(self, analysis_data: Dict) -> str:
        return "Analysis of design patterns used in the codebase will be based on code structure and architecture."
    
    def _generate_scalability_notes(self, structure: Dict) -> str:
        return "Scalability considerations based on the current architecture and implementation patterns."
    
    def _generate_endpoints_table(self, endpoints: List) -> str:
        if not endpoints:
            return "No API endpoints detected."
        
        content = "| Endpoint | Method | File | Framework |\n|----------|--------|------|----------|\n"
        for endpoint in endpoints[:20]:  # Limit to first 20
            content += f"| {endpoint.get('endpoint', 'N/A')} | N/A | {endpoint.get('file', 'N/A')} | {endpoint.get('framework', 'N/A')} |\n"
        return content
    
    def _generate_endpoint_details(self, endpoints: List) -> str:
        if not endpoints:
            return "No endpoint details available."
        return "Detailed endpoint documentation will be generated based on code analysis."
    
    def _generate_auth_section(self, analysis_data: Dict) -> str:
        return "Authentication mechanisms will be documented based on code analysis."
    
    def _generate_rate_limiting_section(self) -> str:
        return "Rate limiting information will be documented if implemented."
    
    def _generate_error_handling_section(self) -> str:
        return "Error handling patterns will be documented based on code analysis."
    
    def _generate_api_examples(self, endpoints: List) -> str:
        return "Code examples will be generated for each API endpoint."
    
    def _generate_components_overview(self, files_analysis: List) -> str:
        return f"The codebase contains {len(files_analysis)} analyzed components."
    
    def _generate_component_details(self, files_analysis: List) -> str:
        content = ""
        for analysis in files_analysis[:10]:  # Limit to first 10
            if analysis.get("status") == "success":
                file_analysis = analysis.get("analysis", {})
                content += f"### {file_analysis.get('file_path', 'Unknown')}\n"
                content += f"- Language: {file_analysis.get('language', 'Unknown')}\n"
                content += f"- Functions: {len(file_analysis.get('functions', []))}\n"
                content += f"- Classes: {len(file_analysis.get('classes', []))}\n\n"
        return content
    
    def _generate_component_relationships(self, files_analysis: List) -> str:
        return "Component relationships will be mapped based on import/export analysis."
    
    def _generate_testing_guidelines(self, analysis_data: Dict) -> str:
        return "Testing guidelines based on existing test patterns and best practices."
    
    def _generate_prerequisites(self, dependencies: Dict, structure: Dict) -> str:
        project_type = structure.get("project_type", "unknown")
        if project_type == "python":
            return "- Python 3.8 or higher\n- pip package manager"
        elif project_type == "node.js":
            return "- Node.js 16 or higher\n- npm or yarn package manager"
        else:
            return "Prerequisites will be determined based on project analysis."
    
    def _generate_installation_steps(self, dependencies: Dict, structure: Dict) -> str:
        project_type = structure.get("project_type", "unknown")
        if project_type == "python":
            return "1. Clone the repository\n2. Create virtual environment\n3. Install dependencies with pip\n4. Configure environment variables"
        elif project_type == "node.js":
            return "1. Clone the repository\n2. Install dependencies with npm\n3. Configure environment variables\n4. Build the project"
        else:
            return "Installation steps will be determined based on project type."
    
    def _generate_configuration_section(self, analysis_data: Dict) -> str:
        return "Configuration options and environment variables will be documented."
    
    def _generate_environment_setup(self, structure: Dict) -> str:
        return "Environment setup instructions based on project requirements."
    
    def _generate_verification_steps(self, structure: Dict) -> str:
        return "Steps to verify successful installation and setup."
    
    def _generate_troubleshooting_section(self) -> str:
        return "Common issues and their solutions will be documented."
    
    def _generate_data_flow_overview(self, data_flows: Dict) -> str:
        content = "This document describes how data flows through the application.\n\n"
        for flow_type, flows in data_flows.items():
            content += f"- **{flow_type.replace('_', ' ').title()}**: {len(flows)} instances\n"
        return content
    
    def _generate_database_operations(self, db_operations: List) -> str:
        if not db_operations:
            return "No database operations detected."
        content = f"Found {len(db_operations)} database operations:\n\n"
        for op in db_operations[:10]:
            content += f"- File: {op.get('file')}\n  Statement: `{op.get('statement')}`\n\n"
        return content
    
    def _generate_api_interactions(self, api_calls: List) -> str:
        if not api_calls:
            return "No external API calls detected."
        content = f"Found {len(api_calls)} API interactions:\n\n"
        for call in api_calls[:10]:
            content += f"- File: {call.get('file')}\n  Statement: `{call.get('statement')}`\n\n"
        return content
    
    def _generate_file_operations(self, file_ops: List) -> str:
        if not file_ops:
            return "No file operations detected."
        content = f"Found {len(file_ops)} file operations:\n\n"
        for op in file_ops[:10]:
            content += f"- File: {op.get('file')}\n  Statement: `{op.get('statement')}`\n\n"
        return content
    
    def _generate_data_transformations(self, transformations: List) -> str:
        return "Data transformation patterns will be documented based on code analysis."
    
    def _generate_security_considerations(self) -> str:
        return "Security considerations for data handling and storage."
    
    def _generate_project_summary(self, structure: Dict, dependencies: Dict) -> str:
        return f"This is a {structure.get('project_type', 'multi-language')} project with {len(structure.get('languages', {}))} programming languages."
    
    def _generate_key_features(self, analysis_data: Dict) -> str:
        return "Key features will be identified based on code analysis and project structure."
    
    def _generate_technology_stack(self, dependencies: Dict, structure: Dict) -> str:
        content = "### Technologies Used\n"
        for lang in structure.get("languages", {}).keys():
            content += f"- {lang}\n"
        return content
    
    def _generate_project_structure_overview(self, structure: Dict) -> str:
        content = "### Directory Structure\n"
        content += f"- Entry points: {len(structure.get('entry_points', []))}\n"
        content += f"- Configuration files: {len(structure.get('config_files', []))}\n"
        content += f"- Test files: {len(structure.get('test_files', []))}\n"
        return content
    
    def _generate_getting_started(self, structure: Dict) -> str:
        return "Quick start guide for developers new to the project."
    
    def _generate_documentation_index(self) -> str:
        return """### Available Documentation
- Architecture Documentation
- API Documentation  
- Component Documentation
- Setup Guide
- Data Flow Documentation"""
