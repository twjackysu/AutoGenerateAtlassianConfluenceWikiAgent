#!/usr/bin/env python3
"""
Quick start script for Auto-Generate Confluence Wiki Agent
"""
import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import anthropic
        import agents
        import dotenv
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: uv sync")
        return False

def check_environment():
    """Check if environment is configured"""
    required_vars = [
        "ANTHROPIC_API_KEY",
        "CONFLUENCE_URL",
        "CONFLUENCE_USERNAME", 
        "CONFLUENCE_API_TOKEN"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("Please configure your .env file")
        return False
    
    print("✅ Environment configuration is complete")
    return True

def show_quick_start_menu():
    """Show quick start menu"""
    print("\n🚀 Auto-Generate Confluence Wiki Agent")
    print("=" * 50)
    print("Choose an option:")
    print("1. Run example with local directory")
    print("2. Run example with GitHub repository")
    print("3. Show configuration help")
    print("4. Run basic tests")
    print("5. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            return choice
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)

def run_local_example():
    """Run example with local directory"""
    print("\n📂 Running local directory example...")
    os.system("python example_usage.py")

def run_github_example():
    """Run example with GitHub repository"""
    print("\n🌐 GitHub repository example:")
    repo_url = input("Enter GitHub repository URL: ").strip()
    
    if not repo_url:
        print("❌ No repository URL provided")
        return
    
    print(f"Note: You would need to modify example_usage.py to use: {repo_url}")
    print("This feature requires a valid GitHub repository and network access.")

def show_config_help():
    """Show configuration help"""
    print("\n📋 Configuration Help")
    print("=" * 30)
    print("1. Copy .env.example to .env:")
    print("   cp .env.example .env")
    print("\n2. Edit .env with your credentials:")
    print("   - ANTHROPIC_API_KEY: Your Claude API key")
    print("   - CONFLUENCE_URL: Your Confluence instance URL")
    print("   - CONFLUENCE_USERNAME: Your Confluence username")
    print("   - CONFLUENCE_API_TOKEN: Your Confluence API token")
    print("   - MCP_SERVER_URL: MCP server URL (optional)")
    print("\n3. Install dependencies:")
    print("   uv sync")

def run_tests():
    """Run basic tests"""
    print("\n🧪 Running basic tests...")
    if os.path.exists("tests/test_basic.py"):
        os.system("python tests/test_basic.py")
    else:
        print("❌ Test file not found")

def main():
    """Main function"""
    print("🔧 Checking system requirements...")
    
    # Check if .env file exists
    if not Path(".env").exists():
        print("⚠️  .env file not found")
        print("Tip: Copy .env.example to .env and configure your credentials")
    
    # Load environment if .env exists
    if Path(".env").exists():
        from dotenv import load_dotenv
        load_dotenv()
    
    # Check dependencies
    if not check_dependencies():
        print("\nPlease install dependencies first:")
        print("uv sync")
        return
    
    # Check environment
    env_ok = check_environment()
    
    while True:
        choice = show_quick_start_menu()
        
        if choice == "1":
            if env_ok:
                run_local_example()
            else:
                print("❌ Please configure environment first (option 3)")
        
        elif choice == "2":
            if env_ok:
                run_github_example()
            else:
                print("❌ Please configure environment first (option 3)")
        
        elif choice == "3":
            show_config_help()
        
        elif choice == "4":
            run_tests()
        
        elif choice == "5":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
