"""
Query Refinement Agent - Optional agent for clarifying user requirements
"""
from typing import Dict, Any, List
from agents import Agent, Tool
from src.models.claude_model import ClaudeModel

class QueryRefinementAgent:
    """Optional agent for refining and clarifying user queries"""
    
    def __init__(self):
        self.agent = Agent(
            name="Query Refinement Agent",
            instructions="""
            You are a query refinement specialist. Your responsibilities include:
            1. Analyze user requests for documentation generation
            2. Identify ambiguous or unclear requirements
            3. Ask clarifying questions to improve specificity
            4. Suggest documentation types and structures
            5. Help users define their documentation needs precisely
            6. Provide guidance on best practices for technical documentation
            
            Your goal is to ensure that documentation generation requests are clear,
            specific, and will result in useful, targeted documentation.
            """,
            model=ClaudeModel(),
            tools=[
                Tool(
                    name="analyze_user_query",
                    description="Analyze user query for clarity and completeness",
                    function=self.analyze_user_query
                ),
                Tool(
                    name="suggest_documentation_types",
                    description="Suggest appropriate documentation types",
                    function=self.suggest_documentation_types
                ),
                Tool(
                    name="generate_clarifying_questions",
                    description="Generate questions to clarify requirements",
                    function=self.generate_clarifying_questions
                ),
                Tool(
                    name="refine_requirements",
                    description="Refine user requirements based on responses",
                    function=self.refine_requirements
                )
            ]
        )
    
    async def analyze_user_query(self, user_query: str) -> Dict[str, Any]:
        """Analyze user query for clarity and completeness"""
        try:
            analysis = {
                "original_query": user_query,
                "clarity_score": 0,
                "missing_elements": [],
                "ambiguities": [],
                "suggestions": []
            }
            
            # Check for key elements
            key_elements = {
                "repository_location": ["repo", "github", "git", "repository", "code"],
                "documentation_type": ["api", "architecture", "setup", "component", "overview"],
                "target_audience": ["developer", "user", "admin", "stakeholder"],
                "specific_features": ["function", "class", "endpoint", "module"],
                "output_format": ["wiki", "confluence", "markdown"]
            }
            
            found_elements = {}
            for element, keywords in key_elements.items():
                found = any(keyword.lower() in user_query.lower() for keyword in keywords)
                found_elements[element] = found
                if not found:
                    analysis["missing_elements"].append(element)
            
            # Calculate clarity score
            analysis["clarity_score"] = len([v for v in found_elements.values() if v]) / len(key_elements) * 100
            
            # Identify ambiguities
            if ("documentation" in user_query.lower() and 
                not any(doc_type in user_query.lower() for doc_type in ["api", "architecture", "setup", "component"])):
                analysis["ambiguities"].append("Documentation type not specified")
            
            if len(user_query.split()) < 5:
                analysis["ambiguities"].append("Query is very brief and may lack detail")
            
            # Generate suggestions
            if analysis["clarity_score"] < 60:
                analysis["suggestions"] = [
                    "Specify the repository location or URL",
                    "Indicate what type of documentation you need",
                    "Mention your target audience",
                    "Describe any specific components to focus on"
                ]
            
            return {
                "status": "success",
                "analysis": analysis
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to analyze query: {str(e)}"
            }
    
    async def suggest_documentation_types(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest appropriate documentation types based on project analysis"""
        try:
            project_type = project_info.get("project_type", "unknown")
            languages = project_info.get("languages", {})
            has_api = project_info.get("has_api", False)
            
            suggestions = {
                "recommended": [],
                "optional": [],
                "reasoning": {}
            }
            
            # Always recommend overview
            suggestions["recommended"].append({
                "type": "Project Overview",
                "priority": "high",
                "description": "High-level project summary and navigation"
            })
            
            # Architecture documentation for any non-trivial project
            if len(languages) > 1 or project_type != "unknown":
                suggestions["recommended"].append({
                    "type": "Architecture Documentation",
                    "priority": "high",
                    "description": "System design and component relationships"
                })
            
            # API documentation if APIs detected
            if has_api:
                suggestions["recommended"].append({
                    "type": "API Documentation",
                    "priority": "high",
                    "description": "Endpoint documentation and usage examples"
                })
            
            # Setup guide for any project
            suggestions["recommended"].append({
                "type": "Setup Guide",
                "priority": "medium",
                "description": "Installation and configuration instructions"
            })
            
            # Component documentation for complex projects
            if len(languages) > 0:
                suggestions["optional"].append({
                    "type": "Component Documentation",
                    "priority": "medium",
                    "description": "Detailed module and function documentation"
                })
            
            # Data flow for data-intensive projects
            suggestions["optional"].append({
                "type": "Data Flow Documentation",
                "priority": "low",
                "description": "How data moves through the system"
            })
            
            return {
                "status": "success",
                "suggestions": suggestions
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to suggest documentation types: {str(e)}"
            }
    
    async def generate_clarifying_questions(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate questions to clarify requirements"""
        try:
            analysis = analysis_result.get("analysis", {})
            missing_elements = analysis.get("missing_elements", [])
            ambiguities = analysis.get("ambiguities", [])
            
            questions = []
            
            # Questions for missing elements
            if "repository_location" in missing_elements:
                questions.append({
                    "category": "repository",
                    "question": "Where is your code repository located? (GitHub URL, local path, etc.)",
                    "required": True
                })
            
            if "documentation_type" in missing_elements:
                questions.append({
                    "category": "documentation_type",
                    "question": "What type of documentation do you need? (API docs, architecture overview, setup guide, etc.)",
                    "required": True
                })
            
            if "target_audience" in missing_elements:
                questions.append({
                    "category": "audience",
                    "question": "Who is the primary audience for this documentation? (developers, end users, system administrators)",
                    "required": False
                })
            
            if "specific_features" in missing_elements:
                questions.append({
                    "category": "scope",
                    "question": "Are there specific components, modules, or features you want to focus on?",
                    "required": False
                })
            
            # Questions for ambiguities
            if "Documentation type not specified" in ambiguities:
                questions.append({
                    "category": "clarification",
                    "question": "Would you like comprehensive documentation covering all aspects, or focus on specific areas?",
                    "required": False
                })
            
            # Additional helpful questions
            questions.extend([
                {
                    "category": "confluence",
                    "question": "Do you have a specific Confluence space where you'd like to publish the documentation?",
                    "required": False
                },
                {
                    "category": "update_frequency",
                    "question": "How often would you like to update this documentation? (one-time, regular updates)",
                    "required": False
                }
            ])
            
            return {
                "status": "success",
                "questions": questions,
                "total_questions": len(questions),
                "required_questions": len([q for q in questions if q.get("required", False)])
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate clarifying questions: {str(e)}"
            }
    
    async def refine_requirements(self, original_query: str, user_responses: Dict[str, str]) -> Dict[str, Any]:
        """Refine user requirements based on responses to clarifying questions"""
        try:
            refined_requirements = {
                "original_query": original_query,
                "repository_info": {},
                "documentation_scope": {},
                "preferences": {},
                "confluence_settings": {}
            }
            
            # Process repository information
            if "repository" in user_responses:
                repo_info = user_responses["repository"]
                refined_requirements["repository_info"] = {
                    "location": repo_info,
                    "type": "github" if "github.com" in repo_info.lower() else "local"
                }
            
            # Process documentation type preferences
            if "documentation_type" in user_responses:
                doc_types = user_responses["documentation_type"].lower()
                refined_requirements["documentation_scope"] = {
                    "include_api": "api" in doc_types,
                    "include_architecture": "architecture" in doc_types or "design" in doc_types,
                    "include_setup": "setup" in doc_types or "install" in doc_types,
                    "include_components": "component" in doc_types or "module" in doc_types,
                    "comprehensive": "all" in doc_types or "comprehensive" in doc_types
                }
            
            # Process audience information
            if "audience" in user_responses:
                audience = user_responses["audience"].lower()
                refined_requirements["preferences"]["target_audience"] = audience
                refined_requirements["preferences"]["technical_level"] = (
                    "high" if "developer" in audience else
                    "medium" if "admin" in audience else "low"
                )
            
            # Process scope information
            if "scope" in user_responses and user_responses["scope"].strip():
                refined_requirements["documentation_scope"]["focus_areas"] = user_responses["scope"]
            
            # Process Confluence settings
            if "confluence" in user_responses:
                refined_requirements["confluence_settings"]["space"] = user_responses["confluence"]
            
            if "update_frequency" in user_responses:
                refined_requirements["preferences"]["update_frequency"] = user_responses["update_frequency"]
            
            # Generate final refined query
            refined_query = self._generate_refined_query(refined_requirements)
            refined_requirements["refined_query"] = refined_query
            
            return {
                "status": "success",
                "refined_requirements": refined_requirements
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to refine requirements: {str(e)}"
            }
    
    def _generate_refined_query(self, requirements: Dict[str, Any]) -> str:
        """Generate a refined, specific query based on collected requirements"""
        repo_info = requirements.get("repository_info", {})
        doc_scope = requirements.get("documentation_scope", {})
        preferences = requirements.get("preferences", {})
        
        query_parts = []
        
        # Repository
        if repo_info.get("location"):
            query_parts.append(f"Analyze the repository at {repo_info['location']}")
        
        # Documentation types
        doc_types = []
        if doc_scope.get("include_api"):
            doc_types.append("API documentation")
        if doc_scope.get("include_architecture"):
            doc_types.append("architecture documentation")
        if doc_scope.get("include_setup"):
            doc_types.append("setup guide")
        if doc_scope.get("include_components"):
            doc_types.append("component documentation")
        
        if doc_types:
            query_parts.append(f"and generate {', '.join(doc_types)}")
        elif doc_scope.get("comprehensive"):
            query_parts.append("and generate comprehensive documentation")
        
        # Audience
        if preferences.get("target_audience"):
            query_parts.append(f"targeted for {preferences['target_audience']}")
        
        # Focus areas
        if doc_scope.get("focus_areas"):
            query_parts.append(f"with focus on {doc_scope['focus_areas']}")
        
        return " ".join(query_parts) + "."
