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
        """Analyze the GitHub repository twjackysu/JackyAIApp and generate an API endpoint and database interaction report. The report must include a table with the following columns: API Endpoint, Database Tables/Views (leave empty if no database interaction). Focus on identifying which database tables or views each API endpoint accesses.
After generating the report, save the content to Atlassian Confluence under:
Space Key: BIF
Parent Page ID: 1225296267
Page Title: 測試AI 001
If the page already exists, update its content. If it does not exist, create the page.
""",
        max_turns=200
    )
    print("SupervisorAgent Result:")
    
    # Debug: Check what attributes the result object has
    print(f"📊 RunResult attributes: {[attr for attr in dir(supervisor_result) if not attr.startswith('_')]}")
    
    # Safe access to result attributes
    final_output = getattr(supervisor_result, 'final_output', 'No final output available')
    print(f"Final output: {final_output[:1000] + '...' if len(final_output) > 1000 else final_output}")
    
    # Try to access conversation history if available
    if hasattr(supervisor_result, 'messages'):
        print(f"Total turns: {len(supervisor_result.messages)}")
        messages = supervisor_result.messages
    elif hasattr(supervisor_result, 'conversation'):
        print(f"Total turns: {len(supervisor_result.conversation)}")
        messages = supervisor_result.conversation
    elif hasattr(supervisor_result, 'history'):
        print(f"Total turns: {len(supervisor_result.history)}")
        messages = supervisor_result.history
    else:
        print("⚠️ No conversation history available in RunResult")
        messages = []
    
    # Show detailed conversation flow if messages are available
    if messages:
        print("\n🔄 DETAILED MULTI-AGENT CONVERSATION FLOW:")
        print(f"{'='*80}")
        
        for i, message in enumerate(messages, 1):
            role = getattr(message, 'role', 'unknown').upper()
            content = getattr(message, 'content', str(message))
            timestamp = f"Turn {i:02d}"
            
            # Detect agent activities based on message content
            content_lower = content.lower()
            
            if "github" in content_lower or "clone" in content_lower or "repository" in content_lower:
                agent_activity = "🐙 [GithubAgent Activity]"
            elif "scan" in content_lower or "files" in content_lower or "read" in content_lower:
                agent_activity = "🔍 [CodeExplorerAgent Activity]"
            elif "analysis" in content_lower or "pattern" in content_lower or "api" in content_lower:
                agent_activity = "📊 [AnalysisAgent Activity]"
            elif "report" in content_lower or "markdown" in content_lower or "generate" in content_lower:
                agent_activity = "📄 [ReportAgent Activity]"
            elif "save" in content_lower or "upload" in content_lower or "confluence" in content_lower:
                agent_activity = "💾 [SaveOrUploadReportAgent Activity]"
            else:
                agent_activity = "🤖 [SupervisorAgent Activity]"
            
            print(f"\n[{timestamp}] {agent_activity}")
            print(f"Role: {role}")
            
            # Show content with smart truncation
            if len(content) > 300:
                lines = content.split('\n')
                if len(lines) > 5:
                    content_preview = '\n'.join(lines[:3]) + f"\n... ({len(lines)-3} more lines) ..." + '\n'.join(lines[-2:])
                else:
                    content_preview = content[:300] + "..."
            else:
                content_preview = content
                
            print(f"Content: {content_preview}")
            print(f"{'-'*60}")
    
    # Check if workflow completed successfully
    print(f"\n{'='*80}")
    print("🏁 WORKFLOW COMPLETION ANALYSIS:")
    
    final_content = final_output.lower()
    completed_indicators = {
        "Repository cloned": "github" in final_content or "clone" in final_content,
        "Files analyzed": "analysis" in final_content or "files" in final_content,
        "Report generated": "report" in final_content or "markdown" in final_content,
        "Saved locally": "save" in final_content or "test_reports" in final_content
    }
    
    for indicator, status in completed_indicators.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {indicator}: {'Completed' if status else 'Not detected'}")
    
    overall_success = sum(completed_indicators.values()) >= 3
    print(f"\n{'✅ WORKFLOW COMPLETED SUCCESSFULLY!' if overall_success else '⚠️ WORKFLOW MAY BE INCOMPLETE'}")
    print(f"Completion score: {sum(completed_indicators.values())}/4 steps")
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