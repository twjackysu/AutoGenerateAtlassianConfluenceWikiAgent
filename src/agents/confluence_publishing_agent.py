"""
Confluence Publishing Agent - Responsible for publishing documentation to Atlassian Confluence
Uses Atlassian MCP Server for Confluence integration
"""
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
from agents import Agent, Tool
from src.models.claude_model import ClaudeModel
from src.config import config
import json

class ConfluencePublishingAgent:
    """Agent responsible for publishing documentation to Confluence via MCP Server"""
    
    def __init__(self):
        self.agent = Agent(
            name="Confluence Publishing Agent",
            instructions="""
            You are a Confluence publishing specialist. Your responsibilities include:
            1. Connect to Atlassian Confluence via MCP Server
            2. Format documentation for Confluence Wiki markup
            3. Create and organize Confluence pages and spaces
            4. Manage page hierarchies and navigation
            5. Update existing pages or create new ones
            6. Handle attachments and media content
            7. Set appropriate page permissions and metadata
            
            Ensure all documentation is properly formatted for Confluence and follows
            organizational standards for wiki structure and presentation.
            """,
            model=ClaudeModel(),
            tools=[
                Tool(
                    name="connect_to_confluence",
                    description="Establish connection to Confluence via MCP Server",
                    function=self.connect_to_confluence
                ),
                Tool(
                    name="create_confluence_space",
                    description="Create a new Confluence space for the project",
                    function=self.create_confluence_space
                ),
                Tool(
                    name="format_for_confluence",
                    description="Format markdown content for Confluence wiki markup",
                    function=self.format_for_confluence
                ),
                Tool(
                    name="publish_page",
                    description="Publish a single page to Confluence",
                    function=self.publish_page
                ),
                Tool(
                    name="create_page_hierarchy",
                    description="Create a hierarchical structure of pages",
                    function=self.create_page_hierarchy
                ),
                Tool(
                    name="update_existing_page",
                    description="Update an existing Confluence page",
                    function=self.update_existing_page
                ),
                Tool(
                    name="setup_navigation",
                    description="Setup navigation and page structure",
                    function=self.setup_navigation
                )
            ]
        )
        self.mcp_client = None
        self.confluence_connection = None
    
    async def connect_to_confluence(self, mcp_server_config: Dict[str, Any]) -> Dict[str, Any]:
        """Establish connection to Confluence via MCP Server"""
        try:
            # Initialize MCP client connection to Atlassian server
            # This would connect to the remote MCP server that handles Confluence operations
            
            connection_params = {
                "server_url": config.confluence_url,
                "username": config.confluence_username,
                "api_token": config.confluence_api_token,
                "mcp_server": mcp_server_config.get("mcp_server_url", config.mcp_server_url)
            }
            
            # Simulate MCP connection initialization
            # In actual implementation, this would use the MCP protocol
            self.confluence_connection = {
                "status": "connected",
                "server": connection_params["server_url"],
                "user": connection_params["username"],
                "mcp_server": connection_params["mcp_server"],
                "connected_at": datetime.now().isoformat()
            }
            
            return {
                "status": "success",
                "message": "Successfully connected to Confluence via MCP Server",
                "connection_info": self.confluence_connection
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to connect to Confluence: {str(e)}"
            }
    
    async def create_confluence_space(self, space_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Confluence space for the project"""
        try:
            if not self.confluence_connection:
                return {
                    "status": "error",
                    "message": "Not connected to Confluence. Please connect first."
                }
            
            space_key = space_config.get("space_key", "AUTOCODE")
            space_name = space_config.get("space_name", "Auto-Generated Code Documentation")
            space_description = space_config.get("description", "Automatically generated documentation for codebase analysis")
            
            # MCP call to create space
            space_data = {
                "key": space_key,
                "name": space_name,
                "description": space_description,
                "type": "global"
            }
            
            # Simulate MCP call
            # In actual implementation: await self.mcp_client.call("confluence.create_space", space_data)
            created_space = {
                "id": "12345",
                "key": space_key,
                "name": space_name,
                "description": space_description,
                "homepage": {
                    "id": "67890",
                    "title": f"{space_name} - Home"
                },
                "created_at": datetime.now().isoformat()
            }
            
            return {
                "status": "success",
                "message": f"Successfully created Confluence space: {space_name}",
                "space": created_space
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to create Confluence space: {str(e)}"
            }
    
    async def format_for_confluence(self, markdown_content: str, page_title: str) -> Dict[str, Any]:
        """Format markdown content for Confluence wiki markup"""
        try:
            # Convert Markdown to Confluence Storage Format
            confluence_content = self._convert_markdown_to_confluence(markdown_content)
            
            # Add Confluence-specific formatting
            formatted_content = self._add_confluence_formatting(confluence_content, page_title)
            
            return {
                "status": "success",
                "original_content": markdown_content,
                "confluence_content": formatted_content,
                "title": page_title
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to format content for Confluence: {str(e)}"
            }
    
    def _convert_markdown_to_confluence(self, markdown: str) -> str:
        """Convert Markdown to Confluence storage format"""
        # Basic Markdown to Confluence conversion
        confluence = markdown
        
        # Headers
        confluence = confluence.replace("### ", "h3. ")
        confluence = confluence.replace("## ", "h2. ")
        confluence = confluence.replace("# ", "h1. ")
        
        # Code blocks
        confluence = confluence.replace("```python", "{code:language=python}")
        confluence = confluence.replace("```javascript", "{code:language=javascript}")
        confluence = confluence.replace("```", "{code}")
        
        # Inline code
        confluence = confluence.replace("`", "{{")
        confluence = confluence.replace("`", "}}")
        
        # Tables - convert Markdown tables to Confluence
        lines = confluence.split('\n')
        in_table = False
        new_lines = []
        
        for line in lines:
            if '|' in line and not line.strip().startswith('|--'):
                if not in_table:
                    new_lines.append("")  # Add space before table
                    in_table = True
                # Convert Markdown table row to Confluence
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                if cells:
                    confluence_row = "| " + " | ".join(cells) + " |"
                    new_lines.append(confluence_row)
            elif in_table and not '|' in line:
                in_table = False
                new_lines.append("")  # Add space after table
                new_lines.append(line)
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def _add_confluence_formatting(self, content: str, title: str) -> str:
        """Add Confluence-specific formatting and metadata"""
        
        # Add page metadata and formatting
        formatted_content = f"""
{content}

---
{{info}}
This documentation was automatically generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} using the Auto-Generate Confluence Wiki Agent.
{{info}}

{{panel:title=Navigation|borderStyle=dashed|borderColor=#ccc|titleBGColor=#f7f7f7|bgColor=#ffffce}}
* [Architecture Documentation|Architecture Documentation]
* [API Documentation|API Documentation]
* [Component Documentation|Component Documentation]
* [Setup Guide|Setup Guide]
* [Data Flow Documentation|Data Flow Documentation]
{{panel}}
"""
        
        return formatted_content
    
    async def publish_page(self, page_data: Dict[str, Any], space_key: str) -> Dict[str, Any]:
        """Publish a single page to Confluence"""
        try:
            if not self.confluence_connection:
                return {
                    "status": "error",
                    "message": "Not connected to Confluence. Please connect first."
                }
            
            page_title = page_data.get("title", "Untitled Page")
            page_content = page_data.get("content", "")
            parent_page_id = page_data.get("parent_page_id")
            
            # Format content for Confluence
            formatting_result = await self.format_for_confluence(page_content, page_title)
            
            if formatting_result["status"] != "success":
                return formatting_result
            
            confluence_content = formatting_result["confluence_content"]
            
            # Prepare page data for MCP call
            page_create_data = {
                "type": "page",
                "title": page_title,
                "space": {"key": space_key},
                "body": {
                    "storage": {
                        "value": confluence_content,
                        "representation": "storage"
                    }
                }
            }
            
            if parent_page_id:
                page_create_data["ancestors"] = [{"id": parent_page_id}]
            
            # Simulate MCP call to create page
            # In actual implementation: await self.mcp_client.call("confluence.create_page", page_create_data)
            created_page = {
                "id": f"page_{datetime.now().timestamp()}",
                "title": page_title,
                "space": {"key": space_key},
                "version": {"number": 1},
                "created_at": datetime.now().isoformat(),
                "url": f"{config.confluence_url}/spaces/{space_key}/pages/{page_title.replace(' ', '+')}"
            }
            
            return {
                "status": "success",
                "message": f"Successfully published page: {page_title}",
                "page": created_page
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to publish page: {str(e)}"
            }
    
    async def create_page_hierarchy(self, documentation_set: List[Dict[str, Any]], space_key: str) -> Dict[str, Any]:
        """Create a hierarchical structure of pages"""
        try:
            created_pages = []
            page_hierarchy = []
            
            # Define the page hierarchy
            hierarchy_order = [
                "Project Overview",
                "Architecture Documentation", 
                "API Documentation",
                "Component Documentation",
                "Setup and Installation Guide",
                "Data Flow Documentation"
            ]
            
            parent_page_id = None
            
            for doc in documentation_set:
                doc_title = doc.get("title", "")
                
                # Find the order for this document
                if doc_title in hierarchy_order:
                    page_result = await self.publish_page({
                        "title": doc_title,
                        "content": doc.get("content", ""),
                        "parent_page_id": parent_page_id
                    }, space_key)
                    
                    if page_result["status"] == "success":
                        created_pages.append(page_result["page"])
                        page_hierarchy.append({
                            "title": doc_title,
                            "page_id": page_result["page"]["id"],
                            "parent_id": parent_page_id,
                            "order": hierarchy_order.index(doc_title)
                        })
                        
                        # Set first page as parent for subsequent pages
                        if parent_page_id is None:
                            parent_page_id = page_result["page"]["id"]
            
            return {
                "status": "success",
                "message": f"Successfully created page hierarchy with {len(created_pages)} pages",
                "pages": created_pages,
                "hierarchy": page_hierarchy
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to create page hierarchy: {str(e)}"
            }
    
    async def update_existing_page(self, page_id: str, updated_content: str, space_key: str) -> Dict[str, Any]:
        """Update an existing Confluence page"""
        try:
            if not self.confluence_connection:
                return {
                    "status": "error",
                    "message": "Not connected to Confluence. Please connect first."
                }
            
            # Get current page version
            # In actual implementation: current_page = await self.mcp_client.call("confluence.get_page", {"id": page_id})
            current_version = 1  # Simulated
            
            # Format updated content
            formatting_result = await self.format_for_confluence(updated_content, "Updated Page")
            
            if formatting_result["status"] != "success":
                return formatting_result
            
            # Prepare update data
            update_data = {
                "id": page_id,
                "type": "page",
                "version": {"number": current_version + 1},
                "body": {
                    "storage": {
                        "value": formatting_result["confluence_content"],
                        "representation": "storage"
                    }
                }
            }
            
            # Simulate MCP call to update page
            # In actual implementation: await self.mcp_client.call("confluence.update_page", update_data)
            updated_page = {
                "id": page_id,
                "version": {"number": current_version + 1},
                "updated_at": datetime.now().isoformat(),
                "url": f"{config.confluence_url}/pages/{page_id}"
            }
            
            return {
                "status": "success",
                "message": f"Successfully updated page: {page_id}",
                "page": updated_page
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to update page: {str(e)}"
            }
    
    async def setup_navigation(self, space_key: str, page_hierarchy: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Setup navigation and page structure"""
        try:
            # Create navigation page
            navigation_content = self._generate_navigation_content(page_hierarchy)
            
            nav_result = await self.publish_page({
                "title": "Documentation Navigation",
                "content": navigation_content
            }, space_key)
            
            return {
                "status": "success",
                "message": "Successfully setup navigation structure",
                "navigation_page": nav_result.get("page") if nav_result["status"] == "success" else None
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to setup navigation: {str(e)}"
            }
    
    def _generate_navigation_content(self, page_hierarchy: List[Dict[str, Any]]) -> str:
        """Generate navigation content for the documentation"""
        content = """# Documentation Navigation

This page provides an overview and navigation for all auto-generated documentation.

## Documentation Structure

"""
        
        for page in sorted(page_hierarchy, key=lambda x: x.get("order", 999)):
            title = page.get("title", "Unknown")
            content += f"### [{title}|{title}]\n"
            content += f"Navigate to the {title.lower()} section.\n\n"
        
        content += """
## How to Use This Documentation

1. **Start with the Project Overview** to understand the overall project structure
2. **Review the Architecture Documentation** for technical design details
3. **Check the API Documentation** for endpoint information
4. **Explore Component Documentation** for detailed module information
5. **Follow the Setup Guide** for installation instructions
6. **Study Data Flow Documentation** for understanding data movement

## Last Updated
This navigation was generated on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return content
