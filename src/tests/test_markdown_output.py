import asyncio
from dotenv import load_dotenv
from agents import Runner
from src.agents.smart_codebase_agent import smart_codebase_agent

load_dotenv()

async def test_markdown_output():
    """Test the new markdown output feature"""
    
    # Test 1: Analysis with file output
    print("🧪 Testing markdown output to file...")
    result = await Runner.run(
        smart_codebase_agent,
        "Please analyze the repository './repos/JackyAIApp' and save the analysis to './analysis_output' folder."
    )
    print("Result:", result.final_output)
    
    # Test 2: Analysis without file output (console only)
    print("\n🧪 Testing console-only output...")
    result = await Runner.run(
        smart_codebase_agent,
        "Please analyze the repository './repos/JackyAIApp' focusing on architecture only."
    )
    print("Result:", result.final_output[:500] + "..." if len(result.final_output) > 500 else result.final_output)
    
    # Clean up connections if needed
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_markdown_output())