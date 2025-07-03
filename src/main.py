"""
Main Application Controller - Orchestrates all agents to generate documentation
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from agents import Agent, Runner
from src.config import config
from src.models.claude_model import ClaudeModel
from src.agents.code_retrieval_agent import CodeRetrievalAgent
from src.agents.codebase_analysis_agent import CodebaseAnalysisAgent
from src.agents.documentation_generation_agent import DocumentationGenerationAgent
from src.agents.confluence_publishing_agent import ConfluencePublishingAgent
from src.agents.query_refinement_agent import QueryRefinementAgent

class WikiGenerationOrchestrator:
    """Main orchestrator for the auto-generation workflow"""
    
    def __init__(self):
        # Initialize all agents
        self.code_retrieval_agent = CodeRetrievalAgent()
        self.codebase_analysis_agent = CodebaseAnalysisAgent()
        self.documentation_generation_agent = DocumentationGenerationAgent()
        self.confluence_publishing_agent = ConfluencePublishingAgent()
        self.query_refinement_agent = QueryRefinementAgent()
        
        # Main orchestrator agent
        self.orchestrator = Agent(
            name="Wiki Generation Orchestrator",
            instructions="""
            You are the main orchestrator for auto-generating Confluence wiki documentation.
            You coordinate between multiple specialized agents to:
            1. Retrieve and analyze code repositories
            2. Generate comprehensive documentation
            3. Publish content to Confluence
            
            Ensure all steps are completed successfully and handle any errors gracefully.
            Provide clear progress updates and final results to users.
            """,
            model=ClaudeModel()
        )
    
    async def generate_wiki_documentation(self, user_request: Dict[str, Any]) -> Dict[str, Any]:
        """Main workflow to generate wiki documentation"""
        try:
            workflow_start = datetime.now()
            results = {
                "workflow_id": f"wiki_gen_{int(workflow_start.timestamp())}",
                "started_at": workflow_start.isoformat(),
                "status": "in_progress",
                "steps": {},
                "final_result": None
            }
            
            print(f"🚀 Starting wiki generation workflow: {results['workflow_id']}")
            
            # Step 1: Query Refinement (if needed)
            if user_request.get("refine_query", False):
                print("📝 Step 1: Refining user query...")
                refinement_result = await self._refine_user_query(user_request)
                results["steps"]["query_refinement"] = refinement_result
                
                if refinement_result["status"] != "success":
                    results["status"] = "failed"
                    results["error"] = "Query refinement failed"
                    return results
                
                # Update user request with refined requirements
                user_request.update(refinement_result.get("refined_requirements", {}))
            
            # Step 2: Code Retrieval
            print("📂 Step 2: Retrieving code repository...")
            retrieval_result = await self._retrieve_code(user_request)
            results["steps"]["code_retrieval"] = retrieval_result
            
            if retrieval_result["status"] != "success":
                results["status"] = "failed"
                results["error"] = "Code retrieval failed"
                return results
            
            # Step 3: Codebase Analysis
            print("🔍 Step 3: Analyzing codebase...")
            analysis_result = await self._analyze_codebase(retrieval_result["files"])
            results["steps"]["codebase_analysis"] = analysis_result
            
            if analysis_result["status"] != "success":
                results["status"] = "failed"
                results["error"] = "Codebase analysis failed"
                return results
            
            # Step 4: Documentation Generation
            print("📚 Step 4: Generating documentation...")
            documentation_result = await self._generate_documentation(analysis_result, user_request)
            results["steps"]["documentation_generation"] = documentation_result
            
            if documentation_result["status"] != "success":
                results["status"] = "failed"
                results["error"] = "Documentation generation failed"
                return results
            
            # Step 5: Confluence Publishing
            print("🌐 Step 5: Publishing to Confluence...")
            publishing_result = await self._publish_to_confluence(documentation_result["documents"], user_request)
            results["steps"]["confluence_publishing"] = publishing_result
            
            if publishing_result["status"] != "success":
                results["status"] = "failed"
                results["error"] = "Confluence publishing failed"
                return results
            
            # Workflow completed successfully
            results["status"] = "completed"
            results["completed_at"] = datetime.now().isoformat()
            results["final_result"] = {
                "confluence_space": publishing_result.get("space_key"),
                "created_pages": len(publishing_result.get("pages", [])),
                "documentation_url": publishing_result.get("space_url"),
                "total_processing_time": (datetime.now() - workflow_start).total_seconds()
            }
            
            print(f"✅ Wiki generation completed successfully!")
            print(f"📖 Created {results['final_result']['created_pages']} pages in Confluence")
            print(f"⏱️ Total time: {results['final_result']['total_processing_time']:.2f} seconds")
            
            return results
            
        except Exception as e:
            results["status"] = "failed"
            results["error"] = f"Workflow failed: {str(e)}"
            results["failed_at"] = datetime.now().isoformat()
            print(f"❌ Workflow failed: {str(e)}")
            return results
    
    async def _refine_user_query(self, user_request: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Refine user query for clarity"""
        try:
            query = user_request.get("query", "")
            
            # Analyze the query
            analysis_result = await self.query_refinement_agent.analyze_user_query(query)
            
            if analysis_result["status"] != "success":
                return analysis_result
            
            analysis = analysis_result["analysis"]
            
            # If clarity score is high enough, skip refinement
            if analysis["clarity_score"] >= 80:
                return {
                    "status": "success",
                    "message": "Query is clear enough, no refinement needed",
                    "analysis": analysis
                }
            
            # Generate clarifying questions
            questions_result = await self.query_refinement_agent.generate_clarifying_questions(analysis_result)
            
            if questions_result["status"] != "success":
                return questions_result
            
            # In a real implementation, you would present these questions to the user
            # For now, we'll use default responses
            default_responses = self._get_default_responses(user_request)
            
            # Refine requirements
            refined_result = await self.query_refinement_agent.refine_requirements(query, default_responses)
            
            return refined_result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Query refinement failed: {str(e)}"
            }
    
    def _get_default_responses(self, user_request: Dict[str, Any]) -> Dict[str, str]:
        """Generate default responses for missing information"""
        responses = {}
        
        if "repository" in user_request:
            responses["repository"] = user_request["repository"]
        
        responses["documentation_type"] = user_request.get("doc_types", "comprehensive documentation")
        responses["audience"] = user_request.get("audience", "developers")
        responses["confluence"] = user_request.get("confluence_space", "AUTO-DOCS")
        
        return responses
    
    async def _retrieve_code(self, user_request: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: Retrieve code from repository"""
        try:
            repository_info = user_request.get("repository_info", {})
            repo_location = repository_info.get("location") or user_request.get("repository")
            
            if not repo_location:
                return {
                    "status": "error",
                    "message": "No repository location specified"
                }
            
            # Determine if it's a remote or local repository
            if repo_location.startswith(("http", "git@")):
                # Clone remote repository
                clone_result = await self.code_retrieval_agent.clone_repository(repo_location)
                
                if clone_result["status"] != "success":
                    return clone_result
                
                local_path = clone_result["local_path"]
            else:
                # Use local directory
                local_path = repo_location
            
            # Read and index files
            files_result = await self.code_retrieval_agent.read_local_directory(local_path)
            
            if files_result["status"] != "success":
                return files_result
            
            # Get content for all files
            files_with_content = []
            for file_info in files_result["files"]:
                content_result = await self.code_retrieval_agent.get_file_content(file_info["path"])
                
                if content_result["status"] == "success":
                    files_with_content.append({
                        **file_info,
                        "content": content_result["content"]
                    })
            
            return {
                "status": "success",
                "repository": repo_location,
                "local_path": local_path,
                "total_files": len(files_with_content),
                "files": files_with_content
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Code retrieval failed: {str(e)}"
            }
    
    async def _analyze_codebase(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Step 3: Analyze the codebase structure and dependencies"""
        try:
            analysis_results = {
                "files_analysis": [],
                "dependencies": {},
                "structure": {},
                "api_endpoints": [],
                "data_flows": {}
            }
            
            # Analyze individual files
            for file_data in files_data[:50]:  # Limit to first 50 files for performance
                file_path = file_data["path"]
                content = file_data["content"]
                
                if file_path.endswith('.py'):
                    file_analysis = await self.codebase_analysis_agent.analyze_python_file(file_path, content)
                elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
                    file_analysis = await self.codebase_analysis_agent.analyze_javascript_file(file_path, content)
                else:
                    continue
                
                if file_analysis["status"] == "success":
                    analysis_results["files_analysis"].append(file_analysis)
            
            # Extract dependencies
            deps_result = await self.codebase_analysis_agent.extract_dependencies(files_data)
            if deps_result["status"] == "success":
                analysis_results["dependencies"] = deps_result["dependencies"]
            
            # Analyze project structure
            structure_result = await self.codebase_analysis_agent.analyze_project_structure(files_data)
            if structure_result["status"] == "success":
                analysis_results["structure"] = structure_result["structure"]
            
            # Identify API endpoints
            api_result = await self.codebase_analysis_agent.identify_api_endpoints(files_data)
            if api_result["status"] == "success":
                analysis_results["api_endpoints"] = api_result["endpoints"]
            
            # Map data flows
            flow_result = await self.codebase_analysis_agent.map_data_flows(files_data)
            if flow_result["status"] == "success":
                analysis_results["data_flows"] = flow_result["data_flows"]
            
            return {
                "status": "success",
                "analysis": analysis_results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Codebase analysis failed: {str(e)}"
            }
    
    async def _generate_documentation(self, analysis_result: Dict[str, Any], user_request: Dict[str, Any]) -> Dict[str, Any]:
        """Step 4: Generate documentation based on analysis"""
        try:
            analysis_data = analysis_result["analysis"]
            documentation_scope = user_request.get("documentation_scope", {})
            
            documents = []
            
            # Generate overview documentation (always included)
            overview_result = await self.documentation_generation_agent.create_overview_doc(analysis_data, user_request)
            if overview_result["status"] == "success":
                documents.append(overview_result["document"])
            
            # Generate architecture documentation
            if documentation_scope.get("include_architecture", True):
                arch_result = await self.documentation_generation_agent.generate_architecture_doc(analysis_data, user_request)
                if arch_result["status"] == "success":
                    documents.append(arch_result["document"])
            
            # Generate API documentation
            if documentation_scope.get("include_api", True) and analysis_data.get("api_endpoints"):
                api_result = await self.documentation_generation_agent.generate_api_documentation(analysis_data, user_request)
                if api_result["status"] == "success":
                    documents.append(api_result["document"])
            
            # Generate component documentation
            if documentation_scope.get("include_components", True):
                comp_result = await self.documentation_generation_agent.generate_component_docs(analysis_data, user_request)
                if comp_result["status"] == "success":
                    documents.append(comp_result["document"])
            
            # Generate setup guide
            if documentation_scope.get("include_setup", True):
                setup_result = await self.documentation_generation_agent.generate_setup_guide(analysis_data, user_request)
                if setup_result["status"] == "success":
                    documents.append(setup_result["document"])
            
            # Generate data flow documentation
            if documentation_scope.get("include_data_flow", False) and analysis_data.get("data_flows"):
                flow_result = await self.documentation_generation_agent.generate_data_flow_docs(analysis_data, user_request)
                if flow_result["status"] == "success":
                    documents.append(flow_result["document"])
            
            return {
                "status": "success",
                "total_documents": len(documents),
                "documents": documents
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Documentation generation failed: {str(e)}"
            }
    
    async def _publish_to_confluence(self, documents: List[Dict[str, Any]], user_request: Dict[str, Any]) -> Dict[str, Any]:
        """Step 5: Publish documentation to Confluence"""
        try:
            confluence_settings = user_request.get("confluence_settings", {})
            space_key = confluence_settings.get("space", "AUTO-DOCS")
            
            # Connect to Confluence
            mcp_config = {"mcp_server_url": config.mcp_server_url}
            connection_result = await self.confluence_publishing_agent.connect_to_confluence(mcp_config)
            
            if connection_result["status"] != "success":
                return connection_result
            
            # Create or use existing space
            space_config = {
                "space_key": space_key,
                "space_name": f"Auto-Generated Documentation - {datetime.now().strftime('%Y-%m-%d')}",
                "description": "Automatically generated documentation for codebase analysis"
            }
            
            space_result = await self.confluence_publishing_agent.create_confluence_space(space_config)
            
            if space_result["status"] != "success":
                return space_result
            
            # Create page hierarchy
            hierarchy_result = await self.confluence_publishing_agent.create_page_hierarchy(documents, space_key)
            
            if hierarchy_result["status"] != "success":
                return hierarchy_result
            
            # Setup navigation
            nav_result = await self.confluence_publishing_agent.setup_navigation(space_key, hierarchy_result["hierarchy"])
            
            return {
                "status": "success",
                "space_key": space_key,
                "space_url": f"{config.confluence_url}/spaces/{space_key}",
                "pages": hierarchy_result["pages"],
                "navigation": nav_result.get("navigation_page")
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Confluence publishing failed: {str(e)}"
            }

# Main entry point
async def main():
    """Main entry point for the application"""
    try:
        # Validate configuration
        config.validate_config()
        
        # Create orchestrator
        orchestrator = WikiGenerationOrchestrator()
        
        # Example user request
        user_request = {
            "repository": "https://github.com/example/project.git",  # Replace with actual repo
            "documentation_scope": {
                "include_architecture": True,
                "include_api": True,
                "include_components": True,
                "include_setup": True,
                "include_data_flow": True
            },
            "confluence_settings": {
                "space": "AUTO-DOCS"
            },
            "preferences": {
                "target_audience": "developers",
                "technical_level": "high"
            }
        }
        
        # Run the workflow
        result = await orchestrator.generate_wiki_documentation(user_request)
        
        print("\n📊 Final Results:")
        print(f"Status: {result['status']}")
        if result['status'] == 'completed':
            final_result = result['final_result']
            print(f"Confluence Space: {final_result['confluence_space']}")
            print(f"Created Pages: {final_result['created_pages']}")
            print(f"Documentation URL: {final_result['documentation_url']}")
            print(f"Processing Time: {final_result['total_processing_time']:.2f} seconds")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Application failed: {str(e)}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    asyncio.run(main())
