#!/usr/bin/env python3
"""
Test script for the multi-agent codebase analysis system.
This test demonstrates the new multi-agent architecture with coordinated agents.
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

from openai import AsyncOpenAI
from agents import Runner, set_default_openai_api, set_default_openai_client, set_tracing_disabled
from src.ai_agents.supervisor_agent import supervisor_agent

# Check if OpenAI API key is available
# if not os.getenv('OPENAI_API_KEY'):
#     print("❌ Error: OPENAI_API_KEY environment variable is not set!")
#     print("Please create a .env file in the project root with:")
#     print("OPENAI_API_KEY=your_openai_api_key_here")
#     exit(1)

BASE_URL = os.getenv("CUSTOM_AI_ENDPOINT") or ""
API_KEY = os.getenv("CUSTOM_AI_ENDPOINT_API_KEY") or ""
MODEL_NAME = os.getenv("DEFAULT_MODEL") or ""

if not BASE_URL or not API_KEY or not MODEL_NAME:
    raise ValueError(
        "Please set CUSTOM_AI_ENDPOINT, CUSTOM_AI_ENDPOINT_API_KEY, DEFAULT_MODEL via env var or code."
    )

client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)
set_default_openai_client(client=client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)

async def test_multi_agent_coordination():
    """Test multi-agent system coordination"""
    print("\n🤖 Testing Multi-Agent System Coordination...")
    print("=" * 60)
    
    # Test 1: SupervisorAgent orchestration
    print("Step 1: Testing SupervisorAgent orchestration...")
    supervisor_result = await Runner.run(
        supervisor_agent,
        "Analyze the GitHub repository 'twjackysu/JackyAIApp' and generate api endpoint reports. The report must include at least one table and contain at least four columns: API Endpoint, File Name, Class Name, and Method Name. Save report to './test_reports/multi_agent/'.",
        max_turns=200
    )
    print("SupervisorAgent Result:")
    print(supervisor_result.final_output[:1000] + "..." if len(supervisor_result.final_output) > 1000 else supervisor_result.final_output)
    print("\n" + "="*60)


async def main():
    """Run all multi-agent tests"""
    print("🧪 Multi-Agent Codebase Analysis System Tests")
    print("=" * 70)
    
    try:
        # Test coordinated multi-agent workflow
        await test_multi_agent_coordination()
        
        print("\n🎉 All multi-agent tests completed!")
        print("The new multi-agent system is ready for use alongside the original comprehensive agent.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())