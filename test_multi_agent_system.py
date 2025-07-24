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

# Auto-switch between OpenAI and Custom AI endpoint
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CUSTOM_AI_ENDPOINT = os.getenv("CUSTOM_AI_ENDPOINT")
CUSTOM_AI_ENDPOINT_API_KEY = os.getenv("CUSTOM_AI_ENDPOINT_API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")

if OPENAI_API_KEY:
    # Priority 1: Use OpenAI API (with tracing support)
    print("🔵 Using OpenAI API (tracing enabled)")
    # OpenAI client will be auto-configured by agents library
else:
    # Priority 2: Use Custom AI endpoint
    print("🟡 Using Custom AI endpoint (tracing disabled)")
    
    if not CUSTOM_AI_ENDPOINT or not CUSTOM_AI_ENDPOINT_API_KEY or not DEFAULT_MODEL:
        raise ValueError(
            "No OPENAI_API_KEY found. Please set CUSTOM_AI_ENDPOINT, CUSTOM_AI_ENDPOINT_API_KEY, DEFAULT_MODEL via env var."
        )
    
    client = AsyncOpenAI(
        base_url=CUSTOM_AI_ENDPOINT,
        api_key=CUSTOM_AI_ENDPOINT_API_KEY,
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
        "Analyze the GitHub repository 'twjackysu/JackyAIApp' and generate an API endpoint and database interaction report. The report must include a table with the following columns: API Endpoint, Database Tables/Views (leave empty if no database interaction). Focus on identifying which database tables or views each API endpoint accesses. Save the report as a markdown file locally in the ./test_reports/ directory.",
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