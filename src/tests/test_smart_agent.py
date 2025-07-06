#!/usr/bin/env python3

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file in project root
env_path = project_root / '.env'
load_dotenv(env_path)

# Check if OpenAI API key is available
if not os.getenv('OPENAI_API_KEY'):
    print("❌ Error: OPENAI_API_KEY environment variable is not set!")
    print("Please create a .env file in the project root with:")
    print("OPENAI_API_KEY=your_openai_api_key_here")
    exit(1)

from agents import Runner
from src.agents.smart_codebase_agent import smart_codebase_agent


async def test_smart_agent():
    """Test the smart codebase agent with automatic size detection"""
    
    print("🧠 Testing Smart Codebase Agent")
    print("=" * 40)
    
    # Test 1: Analyze existing repository
    print("\n🔍 Test 1: Smart analysis of existing repository...")
    result1 = await Runner.run(
        smart_codebase_agent,
        "Please analyze the codebase in './repos/JackyAIApp' and provide insights about its architecture and data sources."
    )
    
    # Save the result
    with open("./smart_analysis_report.md", 'w', encoding='utf-8') as f:
        f.write(result1.final_output)
    
    print(f"✅ Analysis completed and saved to smart_analysis_report.md")
    print(f"📄 Preview:\n{result1.final_output[:500]}...")
    
    # Test 2: Clone and analyze a small repository
    print("\n📥 Test 2: Clone and analyze a small repository...")
    result2 = await Runner.run(
        smart_codebase_agent,
        "Clone the repository 'octocat/Hello-World' and analyze it completely."
    )
    
    # Save the result
    with open("./hello_world_analysis.md", 'w', encoding='utf-8') as f:
        f.write(result2.final_output)
    
    print(f"✅ Small repo analysis completed and saved to hello_world_analysis.md")
    
    # Test 3: Focused analysis request
    print("\n🎯 Test 3: Focused architecture analysis...")
    result3 = await Runner.run(
        smart_codebase_agent,
        "Analyze the architecture of './repos/JackyAIApp' focusing specifically on the frameworks and patterns used."
    )
    
    # Save the result
    with open("./architecture_focused_analysis.md", 'w', encoding='utf-8') as f:
        f.write(result3.final_output)
    
    print(f"✅ Architecture analysis completed and saved to architecture_focused_analysis.md")
    
    print(f"\n📊 Summary:")
    print(f"✅ Smart analysis with auto-sizing")
    print(f"✅ Small repository comprehensive analysis") 
    print(f"✅ Focused architecture analysis")
    
    # Check generated files
    generated_files = [
        "./smart_analysis_report.md",
        "./hello_world_analysis.md", 
        "./architecture_focused_analysis.md"
    ]
    
    print(f"\n📁 Generated Files:")
    for file_path in generated_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✅ {file_path} ({size} bytes)")
        else:
            print(f"  ❌ {file_path} (not found)")


async def interactive_test():
    """Interactive test mode"""
    
    print("\n🎮 Interactive Smart Agent Test")
    print("=" * 35)
    print("Commands:")
    print("  - Just describe what you want to analyze")
    print("  - The agent will automatically determine the best approach")
    print("  - Type 'quit' to exit")
    
    while True:
        try:
            user_input = input("\n💬 What would you like to analyze? ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("🧠 Smart agent analyzing...")
            result = await Runner.run(smart_codebase_agent, user_input)
            
            print(f"\n📄 Analysis Result:")
            print("=" * 50)
            print(result.final_output)
            print("=" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(interactive_test())
    else:
        asyncio.run(test_smart_agent())