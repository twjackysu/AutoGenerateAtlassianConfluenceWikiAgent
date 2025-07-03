"""
Example usage script for the Auto-Generate Confluence Wiki Agent
"""
import asyncio
import os
from pathlib import Path
import sys

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.main import WikiGenerationOrchestrator

async def example_usage():
    """Example of how to use the Wiki Generation Orchestrator"""
    
    print("🔧 Example Usage: Auto-Generate Confluence Wiki")
    print("=" * 50)
    
    # Create orchestrator
    orchestrator = WikiGenerationOrchestrator()
    
    # Example 1: Analyze a local directory
    local_example = {
        "repository": "./src",  # Analyze this project itself
        "documentation_scope": {
            "include_architecture": True,
            "include_api": False,  # No API endpoints in this example
            "include_components": True,
            "include_setup": True,
            "include_data_flow": False
        },
        "confluence_settings": {
            "space": "DEMO-DOCS"
        },
        "preferences": {
            "target_audience": "developers",
            "technical_level": "high"
        }
    }
    
    print("📂 Example 1: Analyzing local directory...")
    print(f"Repository: {local_example['repository']}")
    
    try:
        result = await orchestrator.generate_wiki_documentation(local_example)
        
        if result["status"] == "completed":
            print("✅ Local analysis completed successfully!")
            print(f"Created {result['final_result']['created_pages']} pages")
        else:
            print(f"❌ Local analysis failed: {result.get('error')}")
    
    except Exception as e:
        print(f"💥 Error in local analysis: {str(e)}")
    
    # Example 2: GitHub repository (commented out - requires valid repo)
    """
    github_example = {
        "repository": "https://github.com/openai/openai-python.git",
        "documentation_scope": {
            "include_architecture": True,
            "include_api": True,
            "include_components": True,
            "include_setup": True,
            "include_data_flow": True
        },
        "confluence_settings": {
            "space": "OPENAI-DOCS"
        },
        "preferences": {
            "target_audience": "developers",
            "technical_level": "high"
        }
    }
    
    print("\n🌐 Example 2: Analyzing GitHub repository...")
    print(f"Repository: {github_example['repository']}")
    
    try:
        result = await orchestrator.generate_wiki_documentation(github_example)
        
        if result["status"] == "completed":
            print("✅ GitHub analysis completed successfully!")
            print(f"Documentation URL: {result['final_result']['documentation_url']}")
        else:
            print(f"❌ GitHub analysis failed: {result.get('error')}")
    
    except Exception as e:
        print(f"💥 Error in GitHub analysis: {str(e)}")
    """

def show_configuration_help():
    """Show help for configuration"""
    print("\n📋 Configuration Help")
    print("=" * 30)
    print("Before running this example, make sure you have:")
    print("1. Created a .env file with your API keys")
    print("2. Configured Confluence access")
    print("3. Set up MCP server access")
    print("\nRequired environment variables:")
    print("- ANTHROPIC_API_KEY")
    print("- CONFLUENCE_URL")
    print("- CONFLUENCE_USERNAME") 
    print("- CONFLUENCE_API_TOKEN")
    print("- MCP_SERVER_URL (optional)")

def check_configuration():
    """Check if required configuration is present"""
    required_vars = [
        "ANTHROPIC_API_KEY",
        "CONFLUENCE_URL", 
        "CONFLUENCE_USERNAME",
        "CONFLUENCE_API_TOKEN"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        show_configuration_help()
        return False
    
    print("✅ Configuration check passed!")
    return True

if __name__ == "__main__":
    print("🚀 Auto-Generate Confluence Wiki Agent - Example Usage")
    print("=" * 60)
    
    # Check configuration
    if not check_configuration():
        print("\nPlease configure the required environment variables before running.")
        sys.exit(1)
    
    # Run example
    try:
        asyncio.run(example_usage())
    except KeyboardInterrupt:
        print("\n🛑 Example interrupted by user")
    except Exception as e:
        print(f"\n💥 Example failed: {str(e)}")
        show_configuration_help()
