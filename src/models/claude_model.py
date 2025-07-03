"""
Claude LLM Model wrapper for OpenAI Agent SDK
"""
import asyncio
from typing import Any, Dict, List, Optional, Union

# Temporary mock implementations until packages are installed
try:
    from anthropic import AsyncAnthropic
except ImportError:
    class AsyncAnthropic:
        def __init__(self, api_key: str):
            self.api_key = api_key

try:
    from agents.models.interface import ModelInterface, ModelResponse
    from agents.models.openai_chatcompletions import Message
except ImportError:
    # Mock classes for development
    class ModelInterface:
        pass
    
    class ModelResponse:
        def __init__(self, message, usage):
            self.message = message
            self.usage = usage
    
    class Message:
        def __init__(self, role: str, content: str, tool_calls: Optional[List] = None):
            self.role = role
            self.content = content
            self.tool_calls = tool_calls

from src.config import config

class ClaudeModel(ModelInterface):
    """Claude model implementation for OpenAI Agent SDK"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.claude_model
        self.client = AsyncAnthropic(api_key=config.anthropic_api_key)
    
    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ModelResponse:
        """Complete a chat conversation using Claude"""
        
        # Convert OpenAI format messages to Claude format
        claude_messages = self._convert_messages(messages)
        
        # Prepare the request
        request_params = {
            "model": self.model_name,
            "messages": claude_messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7),
        }
        
        # Add tools if provided
        if tools:
            request_params["tools"] = self._convert_tools(tools)
        
        try:
            response = await self.client.messages.create(**request_params)
            return self._convert_response(response)
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert OpenAI format messages to Claude format"""
        claude_messages = []
        
        for message in messages:
            if message.role == "system":
                # Claude handles system messages differently
                continue
            
            claude_message = {
                "role": message.role,
                "content": message.content
            }
            claude_messages.append(claude_message)
        
        return claude_messages
    
    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI format tools to Claude format"""
        claude_tools = []
        
        for tool in tools:
            if tool.get("type") == "function":
                function = tool.get("function", {})
                claude_tool = {
                    "name": function.get("name"),
                    "description": function.get("description"),
                    "input_schema": function.get("parameters", {})
                }
                claude_tools.append(claude_tool)
        
        return claude_tools
    
    def _convert_response(self, response) -> ModelResponse:
        """Convert Claude response to OpenAI Agent SDK format"""
        
        # Extract content
        content = ""
        tool_calls = []
        
        for content_block in response.content:
            if content_block.type == "text":
                content += content_block.text
            elif content_block.type == "tool_use":
                tool_calls.append({
                    "id": content_block.id,
                    "type": "function",
                    "function": {
                        "name": content_block.name,
                        "arguments": content_block.input
                    }
                })
        
        # Create the response message
        message = Message(
            role="assistant",
            content=content,
            tool_calls=tool_calls if tool_calls else None
        )
        
        return ModelResponse(
            message=message,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
        )
