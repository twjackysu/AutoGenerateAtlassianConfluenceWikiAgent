"""
Configuration module for the Auto-Generate Atlassian Confluence Wiki Agent
"""
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

# Load environment variables
load_dotenv()

class Config(BaseModel):
    """Configuration settings for the application"""
    
    # OpenAI API Key (for Agent SDK)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Anthropic Claude API Key (primary LLM)
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Confluence settings
    confluence_url: str = os.getenv("CONFLUENCE_URL", "")
    confluence_username: str = os.getenv("CONFLUENCE_USERNAME", "")
    confluence_api_token: str = os.getenv("CONFLUENCE_API_TOKEN", "")
    
    # MCP Server settings
    mcp_server_url: str = os.getenv("MCP_SERVER_URL", "")
    
    # Default Claude model
    claude_model: str = "claude-opus-4-20250514"
    
    # Application settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    supported_extensions: list[str] = [
        ".py", ".js", ".ts", ".java", ".go", ".cpp", ".c", ".h", 
        ".jsx", ".tsx", ".vue", ".php", ".rb", ".swift", ".kt", 
        ".rs", ".cs", ".scala", ".clj", ".elm", ".hs"
    ]
    
    def validate_config(self) -> bool:
        """Validate that required configuration is present"""
        required_fields = [
            "anthropic_api_key",
            "confluence_url", 
            "confluence_username",
            "confluence_api_token"
        ]
        
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Missing required configuration: {field}")
        
        return True

# Global configuration instance
config = Config()
