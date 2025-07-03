"""
Auto-Generate Atlassian Confluence Wiki Agent
Main application entry point
"""
import asyncio
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.main import main as app_main

def main():
    print("🚀 Auto-Generate Atlassian Confluence Wiki Agent")
    print("=" * 50)
    
    try:
        # Run the main application
        result = asyncio.run(app_main())
        
        if result["status"] == "completed":
            print("\n✅ Application completed successfully!")
        else:
            print(f"\n❌ Application failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
