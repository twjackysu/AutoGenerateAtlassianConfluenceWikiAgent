"""
Configurable logging system similar to C# NLog
"""

from .logger import get_logger, setup_logging, get_tool_logger

__all__ = ['get_logger', 'setup_logging', 'get_tool_logger']