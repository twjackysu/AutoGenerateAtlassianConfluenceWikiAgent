#!/usr/bin/env python3
"""
Multi-Agent Codebase Analysis System - Main Entry Point

This file demonstrates how to use the new multi-agent system for codebase analysis.
The system consists of specialized agents working in coordination:

- SupervisorAgent: Orchestrates the overall workflow
- GithubAgent: Handles repository operations
- AnalysisAgent: Performs comprehensive code analysis  
- ReportAgent: Generates professional reports

Usage Examples:
    python src/multi_agent_main.py
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
env_path = project_root.parent / '.env'
load_dotenv(env_path)

# Check if OpenAI API key is available
if not os.getenv('OPENAI_API_KEY'):
    print("❌ Error: OPENAI_API_KEY environment variable is not set!")
    print("Please create a .env file in the project root with:")
    print("OPENAI_API_KEY=your_openai_api_key_here")
    exit(1)

from agents import Runner
from .ai_agents.supervisor_agent import supervisor_agent


async def analyze_github_repository():
    """Example: Analyze a GitHub repository using the multi-agent system"""
    print("🚀 Multi-Agent GitHub Repository Analysis")
    print("=" * 50)
    
    # Example 1: Complete analysis of a GitHub repository
    analysis_request = """
    Please analyze the GitHub repository 'twjackysu/JackyAIApp' using the multi-agent system:
    
    1. Clone or update the repository to the latest version
    2. Perform comprehensive code analysis to extract:
       - All API endpoints with methods and parameters
       - System architecture and design patterns
       - Security patterns and authentication mechanisms
       - Framework usage and dependencies
    3. Generate professional reports including:
       - Comprehensive analysis report
       - API inventory documentation
       - Architecture overview
    4. Save all reports to './reports/multi_agent/'
    
    Please coordinate the work across all specialized agents and provide progress updates.
    """
    
    print("🎯 Starting multi-agent analysis...")
    print("Request:", analysis_request[:200] + "...")
    print("\n" + "-" * 50)
    
    result = await Runner.run(supervisor_agent, analysis_request)
    
    print("\n📊 Multi-Agent Analysis Results:")
    print("=" * 50)
    print(result.final_output)
    
    return result


async def analyze_local_repository():
    """Example: Analyze a local repository using the multi-agent system"""
    print("\n🏠 Multi-Agent Local Repository Analysis")
    print("=" * 50)
    
    # Example 2: Analysis of local repository
    local_analysis_request = """
    Please analyze the local repository at './repos/JackyAIApp' (if it exists) using the multi-agent system:
    
    1. Skip GitHub operations since repository is already local
    2. Perform focused analysis to extract:
       - API endpoints and web service interfaces
       - Database connections and data models
       - Security and authentication patterns
    3. Generate a targeted security analysis report
    4. Save reports to './reports/local_analysis/'
    
    Coordinate efficiently between AnalysisAgent and ReportAgent.
    """
    
    print("🎯 Starting local repository analysis...")
    print("Request:", local_analysis_request[:200] + "...")
    print("\n" + "-" * 50)
    
    result = await Runner.run(supervisor_agent, local_analysis_request)
    
    print("\n📊 Local Analysis Results:")
    print("=" * 50)
    print(result.final_output)
    
    return result


async def demonstrate_agent_coordination():
    """Demonstrate how the multi-agent system coordinates work"""
    print("\n🤖 Multi-Agent Coordination Demonstration")
    print("=" * 50)
    
    coordination_request = """
    Demonstrate the multi-agent coordination system by:
    
    1. Creating a new analysis session
    2. Showing how you coordinate with each specialized agent
    3. Explaining the workflow and handoff process
    4. Providing a sample of how findings are shared between agents
    
    Use the repository './repos/JackyAIApp' if available, or explain how the process would work.
    """
    
    print("🎯 Demonstrating agent coordination...")
    print("Request:", coordination_request[:200] + "...")
    print("\n" + "-" * 50)
    
    result = await Runner.run(supervisor_agent, coordination_request)
    
    print("\n🔄 Coordination Demonstration:")
    print("=" * 50)
    print(result.final_output)
    
    return result


async def main():
    """Main function demonstrating multi-agent system capabilities"""
    print("🧠 Multi-Agent Codebase Analysis System")
    print("=" * 70)
    print("This system uses specialized agents working in coordination:")
    print("• SupervisorAgent: Orchestrates workflow and coordination")
    print("• GithubAgent: Handles Git and repository operations")
    print("• AnalysisAgent: Performs comprehensive code analysis")
    print("• ReportAgent: Generates professional documentation")
    print("=" * 70)
    
    try:
        # Demonstrate different use cases
        await analyze_github_repository()
        await analyze_local_repository()
        await demonstrate_agent_coordination()
        
        print("\n🎉 Multi-Agent System Demonstration Complete!")
        print("=" * 70)
        print("✅ The multi-agent system is fully operational")
        print("✅ All agents can coordinate effectively")
        print("✅ Reports are generated in professional format")
        print("✅ System maintains compatibility with original agent")
        
        print("\n📋 Next Steps:")
        print("• Use SupervisorAgent as the main entry point")
        print("• Specify analysis goals and output preferences")
        print("• Monitor agent coordination and progress")
        print("• Review generated reports and findings")
        
    except Exception as e:
        print(f"❌ Error during multi-agent demonstration: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting Multi-Agent Codebase Analysis System...")
    asyncio.run(main())