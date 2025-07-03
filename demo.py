"""
Simplified working demo of the Auto-Generate Confluence Wiki Agent
This version works without external dependencies for demonstration
"""
import asyncio
import os
import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

class SimpleCodeAnalyzer:
    """Simplified code analyzer for demonstration"""
    
    def __init__(self):
        self.supported_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.cpp', '.c']
    
    async def analyze_directory(self, directory_path: str) -> Dict[str, Any]:
        """Analyze a directory and return basic structure info"""
        try:
            path = Path(directory_path)
            if not path.exists():
                return {"status": "error", "message": f"Directory {directory_path} not found"}
            
            analysis = {
                "directory": str(path.absolute()),
                "total_files": 0,
                "code_files": [],
                "languages": {},
                "structure": {
                    "directories": [],
                    "files_by_type": {}
                }
            }
            
            # Walk through directory
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    analysis["total_files"] += 1
                    
                    # Skip hidden files and common non-code directories
                    if any(part.startswith('.') for part in file_path.parts):
                        continue
                    
                    if any(skip_dir in str(file_path) for skip_dir in ['node_modules', '__pycache__', 'venv', 'env']):
                        continue
                    
                    ext = file_path.suffix.lower()
                    if ext in self.supported_extensions:
                        # Count by language
                        analysis["languages"][ext] = analysis["languages"].get(ext, 0) + 1
                        
                        # Add to code files
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                analysis["code_files"].append({
                                    "path": str(file_path),
                                    "name": file_path.name,
                                    "extension": ext,
                                    "size": len(content),
                                    "lines": len(content.split('\n')),
                                    "content_preview": content[:200] + "..." if len(content) > 200 else content
                                })
                        except Exception:
                            continue
            
            return {"status": "success", "analysis": analysis}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

class SimpleDocumentationGenerator:
    """Simplified documentation generator"""
    
    def __init__(self):
        pass
    
    async def generate_overview_doc(self, analysis: Dict[str, Any]) -> str:
        """Generate a project overview document"""
        
        doc = f"""# Project Overview
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Project Summary
This project contains {analysis.get('total_files', 0)} files in total.

## Code Analysis
- **Total Code Files**: {len(analysis.get('code_files', []))}
- **Languages Detected**: {len(analysis.get('languages', {}))}
- **Project Directory**: {analysis.get('directory', 'Unknown')}

## Languages Breakdown
"""
        
        languages = analysis.get('languages', {})
        for ext, count in languages.items():
            language_name = self._get_language_name(ext)
            doc += f"- **{language_name}**: {count} files\n"
        
        doc += f"""
## File Structure Overview
The project contains the following types of code files:

"""
        
        code_files = analysis.get('code_files', [])[:10]  # Show first 10 files
        for file_info in code_files:
            doc += f"### {file_info['name']}\n"
            doc += f"- **Path**: `{file_info['path']}`\n"
            doc += f"- **Size**: {file_info['size']} characters\n"
            doc += f"- **Lines**: {file_info['lines']}\n"
            if file_info.get('content_preview'):
                doc += f"- **Preview**: \n```{file_info['extension'][1:]}\n{file_info['content_preview']}\n```\n\n"
        
        if len(analysis.get('code_files', [])) > 10:
            doc += f"\n... and {len(analysis.get('code_files', [])) - 10} more files.\n"
        
        doc += f"""
## Getting Started
1. This project appears to be a {self._determine_project_type(languages)} project
2. Main languages: {', '.join([self._get_language_name(ext) for ext in languages.keys()])}
3. Consider reviewing the file structure above to understand the project organization

## Next Steps
- Review individual component documentation
- Check setup requirements for this project type
- Examine the codebase for entry points and main functionality

---
*This documentation was automatically generated by the Auto-Generate Confluence Wiki Agent*
"""
        
        return doc
    
    def _get_language_name(self, ext: str) -> str:
        """Convert file extension to language name"""
        mapping = {
            '.py': 'Python',
            '.js': 'JavaScript', 
            '.ts': 'TypeScript',
            '.jsx': 'React JSX',
            '.tsx': 'React TSX',
            '.java': 'Java',
            '.go': 'Go',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby'
        }
        return mapping.get(ext, ext[1:].upper())
    
    def _determine_project_type(self, languages: Dict[str, int]) -> str:
        """Determine project type based on languages"""
        if '.py' in languages:
            return 'Python'
        elif '.js' in languages or '.ts' in languages:
            return 'JavaScript/TypeScript'
        elif '.java' in languages:
            return 'Java'
        elif '.go' in languages:
            return 'Go'
        elif '.cpp' in languages or '.c' in languages:
            return 'C/C++'
        else:
            return 'Multi-language'

class SimpleConfluencePublisher:
    """Simplified Confluence publisher (mock implementation)"""
    
    def __init__(self):
        pass
    
    async def publish_documentation(self, docs: List[str], space_key: str = "DEMO") -> Dict[str, Any]:
        """Mock publishing to Confluence"""
        
        # Save documentation to local files instead
        output_dir = Path("generated_docs")
        output_dir.mkdir(exist_ok=True)
        
        published_files = []
        
        for i, doc in enumerate(docs):
            filename = f"document_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            file_path = output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(doc)
            
            published_files.append({
                "title": f"Document {i+1}",
                "file_path": str(file_path),
                "size": len(doc)
            })
        
        # Also create an index file
        index_content = f"""# Documentation Index
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Generated Documents
"""
        
        for file_info in published_files:
            index_content += f"- [{file_info['title']}]({file_info['file_path']})\n"
        
        index_path = output_dir / "index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        return {
            "status": "success",
            "space_key": space_key,
            "published_files": published_files,
            "index_file": str(index_path),
            "total_documents": len(docs)
        }

class SimpleDemoOrchestrator:
    """Simple demo orchestrator"""
    
    def __init__(self):
        self.analyzer = SimpleCodeAnalyzer()
        self.doc_generator = SimpleDocumentationGenerator()
        self.publisher = SimpleConfluencePublisher()
    
    async def run_demo(self, directory_path: str = "./src") -> Dict[str, Any]:
        """Run a complete demo workflow"""
        
        print(f"🚀 Starting demo analysis of: {directory_path}")
        
        try:
            # Step 1: Analyze code
            print("📂 Step 1: Analyzing codebase...")
            analysis_result = await self.analyzer.analyze_directory(directory_path)
            
            if analysis_result["status"] != "success":
                return analysis_result
            
            analysis = analysis_result["analysis"]
            print(f"✅ Found {len(analysis['code_files'])} code files in {len(analysis['languages'])} languages")
            
            # Step 2: Generate documentation
            print("📚 Step 2: Generating documentation...")
            overview_doc = await self.doc_generator.generate_overview_doc(analysis)
            
            # Step 3: "Publish" documentation (save locally)
            print("🌐 Step 3: Publishing documentation...")
            publish_result = await self.publisher.publish_documentation([overview_doc])
            
            if publish_result["status"] != "success":
                return publish_result
            
            print(f"✅ Demo completed! Generated {publish_result['total_documents']} documents")
            print(f"📁 Documentation saved to: {Path('generated_docs').absolute()}")
            
            return {
                "status": "success",
                "analysis_summary": {
                    "total_files": analysis["total_files"],
                    "code_files": len(analysis["code_files"]),
                    "languages": list(analysis["languages"].keys())
                },
                "documentation": {
                    "generated_docs": publish_result["total_documents"],
                    "output_directory": str(Path("generated_docs").absolute()),
                    "index_file": publish_result["index_file"]
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Demo failed: {str(e)}"
            }

async def main():
    """Main demo function"""
    print("🎯 Auto-Generate Confluence Wiki Agent - Demo Mode")
    print("=" * 60)
    
    orchestrator = SimpleDemoOrchestrator()
    
    # Get directory to analyze
    default_dir = "./src"
    
    print(f"\n📂 Analyzing directory: {default_dir}")
    print("(This is a simplified demo version that works without external APIs)")
    
    result = await orchestrator.run_demo(default_dir)
    
    print(f"\n📊 Demo Results:")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        summary = result['analysis_summary']
        docs = result['documentation']
        
        print(f"\n📈 Analysis Summary:")
        print(f"  - Total files scanned: {summary['total_files']}")
        print(f"  - Code files found: {summary['code_files']}")
        print(f"  - Languages detected: {', '.join(summary['languages'])}")
        
        print(f"\n📚 Documentation Generated:")
        print(f"  - Documents created: {docs['generated_docs']}")
        print(f"  - Output directory: {docs['output_directory']}")
        print(f"  - Index file: {docs['index_file']}")
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"💡 Check the 'generated_docs' folder for your documentation files.")
        
    else:
        print(f"❌ Demo failed: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())
