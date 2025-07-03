"""
Confluence Publishing Agent - Responsible for publishing documentation to Atlassian Confluence
Uses Atlassian MCP Server for Confluence integration
"""
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
from agents import Agent
from agents.mcp.server import MCPServerSse
from src.models.claude_model import ClaudeModel
from src.config import config
import json

class ConfluencePublishingAgent:
    """Agent responsible for publishing documentation to Confluence via MCP Server"""
    
    def __init__(self):
        # Configure the Atlassian MCP Server using SSE transport
        self.mcp_server = MCPServerSse(
            params={
                "url": "https://mcp.atlassian.com/v1/sse",
                "headers": {
                    "jira-url": config.jira_url,
                    "jira-username": config.jira_username, 
                    "jira-token": config.jira_token,
                    "confluence-url": config.confluence_url,
                    "confluence-username": config.confluence_username,
                    "confluence-token": config.confluence_token
                },
                "timeout": 30.0,
                "sse_read_timeout": 300.0
            },
            cache_tools_list=True,
            name="Atlassian MCP Server"
        )
        
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
            
            Use the tools provided by the Atlassian MCP Server to interact with Confluence.
            Always ensure documentation is properly formatted and follows organizational standards.
            """,
            model=ClaudeModel(),
            mcp_servers=[self.mcp_server]
        )
        
        self.confluence_connection = None
    
    async def initialize_connection(self) -> Dict[str, Any]:
        """Initialize the MCP Server connection"""
        try:
            await self.mcp_server.connect()
            self.confluence_connection = {
                "status": "connected",
                "server": config.confluence_url,
                "mcp_server": "https://mcp.atlassian.com/v1/sse",
                "connected_at": datetime.now().isoformat()
            }
            
            return {
                "status": "success",
                "message": "Successfully connected to Atlassian MCP Server",
                "connection_info": self.confluence_connection
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Failed to connect to MCP Server: {str(e)}"
            }
    
    async def cleanup_connection(self):
        """Cleanup the MCP Server connection"""
        if self.mcp_server:
            await self.mcp_server.cleanup()
    
    async def publish_documentation(self, documentation_set: List[Dict[str, Any]], space_key: str = "AUTOCODE") -> Dict[str, Any]:
        """Main method to publish a complete documentation set to Confluence"""
        try:
            # Initialize connection if not already connected
            if not self.confluence_connection:
                init_result = await self.initialize_connection()
                if init_result["status"] != "success":
                    return init_result
            
            results = {
                "status": "success",
                "published_pages": [],
                "errors": []
            }
            
            # Use the agent to process and publish the documentation
            # The agent will use the MCP Server tools automatically
            for doc in documentation_set:
                try:
                    # Let the agent handle the publishing using MCP tools
                    response = await self.agent.run(
                        f"""
                        Please publish the following documentation to Confluence space '{space_key}':
                        
                        Title: {doc.get('title', 'Untitled')}
                        Content: {doc.get('content', '')}
                        
                        Use the Atlassian MCP Server tools to:
                        1. Create the space if it doesn't exist
                        2. Format the content appropriately for Confluence
                        3. Create the page with proper hierarchy
                        4. Set up navigation if needed
                        """
                    )
                    
                    results["published_pages"].append({
                        "title": doc.get('title'),
                        "status": "published",
                        "response": response
                    })
                    
                except Exception as e:
                    results["errors"].append({
                        "title": doc.get('title'),
                        "error": str(e)
                    })
            
            if results["errors"]:
                results["status"] = "partial_success"
            
            return results
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to publish documentation: {str(e)}"
            }
    
    def _convert_markdown_to_confluence(self, markdown: str) -> str:
        """Convert Markdown to Confluence storage format - helper method for local formatting"""
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
        
        # Inline code - fix the replacement pattern
        import re
        confluence = re.sub(r'`([^`]+)`', r'{{\1}}', confluence)
        
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
    
    def _add_confluence_metadata(self, content: str, title: str) -> str:
        """Add Confluence-specific metadata and formatting"""
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
    
    async def test_mcp_connection(self) -> Dict[str, Any]:
        """Test the MCP Server connection and available tools"""
        try:
            # Initialize connection if not already connected
            if not self.confluence_connection:
                init_result = await self.initialize_connection()
                if init_result["status"] != "success":
                    return init_result
            
            # Get available tools from MCP Server
            from agents.run_context import RunContextWrapper
            run_context = RunContextWrapper(context=None)
            tools = await self.mcp_server.list_tools(run_context, self.agent)
            
            return {
                "status": "success",
                "message": "MCP Server connection test successful",
                "available_tools": [tool.name for tool in tools],
                "tool_count": len(tools)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"MCP Server connection test failed: {str(e)}"
            }
