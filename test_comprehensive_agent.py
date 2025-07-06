#!/usr/bin/env python3
"""
Test script for the comprehensive codebase analysis agent
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / '.env'
load_dotenv(env_path)

# Check if OpenAI API key is available
if not os.getenv('OPENAI_API_KEY'):
    print("❌ Error: OPENAI_API_KEY environment variable is not set!")
    print("Please create a .env file in the project root with:")
    print("OPENAI_API_KEY=your_openai_api_key_here")
    exit(1)

from agents import Runner
from src.agents.comprehensive_codebase_agent import comprehensive_codebase_agent


async def test_github_integration():
    """Test GitHub repository analysis"""
    print("\n🐙 Testing GitHub Integration...")
    print("=" * 50)
    
    # Test 1: Clone and list repository contents
    print("Step 1: Testing repository listing...")
    list_result = await Runner.run(
        comprehensive_codebase_agent,
        "Extract all API endpoints and analyze system architecture, use the GitHub repository 'twjackysu/JackyAIApp'. Save reports to './test_reports/'.",
        max_turns=500,  # Increased for comprehensive analysis of large codebases
    )
    print("Repository Analysis Result:")
    print(list_result.final_output[:1000] + "..." if len(list_result.final_output) > 1000 else list_result.final_output)

async def main():
    """Run all tests"""
    print("🧪 Comprehensive Codebase Analysis Agent Tests")
    print("=" * 70)
    
    try:
        # Test GitHub integration
        await test_github_integration()
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())