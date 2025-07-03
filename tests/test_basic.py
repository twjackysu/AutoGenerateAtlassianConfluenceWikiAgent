"""
Basic tests for the Auto-Generate Confluence Wiki Agent
"""
import pytest
import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.config import Config
from src.agents.code_retrieval_agent import CodeRetrievalAgent
from src.agents.codebase_analysis_agent import CodebaseAnalysisAgent

class TestConfig:
    """Test configuration functionality"""
    
    def test_config_creation(self):
        """Test that configuration can be created"""
        config = Config()
        assert config is not None
        assert hasattr(config, 'claude_model')
        assert hasattr(config, 'supported_extensions')
    
    def test_supported_extensions(self):
        """Test that supported extensions are defined"""
        config = Config()
        assert '.py' in config.supported_extensions
        assert '.js' in config.supported_extensions
        assert '.ts' in config.supported_extensions

class TestCodeRetrievalAgent:
    """Test code retrieval functionality"""
    
    @pytest.fixture
    def agent(self):
        """Create a code retrieval agent for testing"""
        return CodeRetrievalAgent()
    
    def test_agent_creation(self, agent):
        """Test that agent can be created"""
        assert agent is not None
        assert agent.agent is not None
        assert agent.agent.name == "Code Retrieval Agent"
    
    @pytest.mark.asyncio
    async def test_list_code_files(self, agent):
        """Test listing code files in current directory"""
        result = await agent.list_code_files("./src")
        
        assert result["status"] == "success"
        assert "files" in result
        assert isinstance(result["files"], list)
        
        # Should find some Python files
        py_files = [f for f in result["files"] if f["extension"] == ".py"]
        assert len(py_files) > 0

class TestCodebaseAnalysisAgent:
    """Test codebase analysis functionality"""
    
    @pytest.fixture
    def agent(self):
        """Create a codebase analysis agent for testing"""
        return CodebaseAnalysisAgent()
    
    def test_agent_creation(self, agent):
        """Test that agent can be created"""
        assert agent is not None
        assert agent.agent is not None
        assert agent.agent.name == "Codebase Analysis Agent"
    
    @pytest.mark.asyncio
    async def test_analyze_python_file(self, agent):
        """Test analyzing a simple Python file"""
        sample_code = '''
def hello_world():
    """A simple hello world function"""
    return "Hello, World!"

class TestClass:
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value
'''
        
        result = await agent.analyze_python_file("test.py", sample_code)
        
        assert result["status"] == "success"
        analysis = result["analysis"]
        
        assert "functions" in analysis
        assert "classes" in analysis
        assert len(analysis["functions"]) == 1
        assert len(analysis["classes"]) == 1
        
        # Check function details
        func = analysis["functions"][0]
        assert func["name"] == "hello_world"
        assert "A simple hello world function" in func["docstring"]
        
        # Check class details
        cls = analysis["classes"][0]
        assert cls["name"] == "TestClass"
        assert "get_value" in cls["methods"]

class TestIntegration:
    """Integration tests for the complete workflow"""
    
    @pytest.mark.asyncio
    async def test_basic_workflow_components(self):
        """Test that all major components can be instantiated"""
        # Test that we can create all agents without errors
        code_agent = CodeRetrievalAgent()
        analysis_agent = CodebaseAnalysisAgent()
        
        assert code_agent is not None
        assert analysis_agent is not None
    
    @pytest.mark.asyncio
    async def test_file_processing_pipeline(self):
        """Test the basic file processing pipeline"""
        # Create agents
        code_agent = CodeRetrievalAgent()
        analysis_agent = CodebaseAnalysisAgent()
        
        # List files in src directory
        files_result = await code_agent.list_code_files("./src")
        assert files_result["status"] == "success"
        
        # Get content of first Python file
        py_files = [f for f in files_result["files"] if f["extension"] == ".py"]
        if py_files:
            first_file = py_files[0]
            content_result = await code_agent.get_file_content(first_file["path"])
            
            if content_result["status"] == "success":
                # Analyze the file
                analysis_result = await analysis_agent.analyze_python_file(
                    first_file["path"], 
                    content_result["content"]
                )
                
                assert analysis_result["status"] == "success"
                assert "analysis" in analysis_result

if __name__ == "__main__":
    print("🧪 Running basic tests...")
    pytest.main([__file__, "-v"])
