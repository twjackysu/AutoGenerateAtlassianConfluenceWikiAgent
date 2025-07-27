"""
Main logging system implementation
Similar to C# NLog with configurable targets and formats
"""

import logging
import logging.config
import os
import yaml
from pathlib import Path
from typing import Optional

# Global flag to ensure logging is only configured once
_logging_configured = False

def setup_logging(config_path: Optional[str] = None, default_level: int = logging.INFO) -> None:
    """
    Setup logging configuration from YAML file
    
    Args:
        config_path: Path to logging configuration file (YAML)
        default_level: Default logging level if config file is not found
    """
    global _logging_configured
    
    if _logging_configured:
        return
    
    # Determine config file path
    if config_path is None:
        # Look for config file in project root
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "logging_config.yaml"
    
    config_path = Path(config_path)
    
    if config_path.exists() and config_path.is_file():
        try:
            # Create logs directory if it doesn't exist
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            
            # Load YAML configuration
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f.read())
            
            # Apply logging configuration
            logging.config.dictConfig(config)
            
            # Log successful configuration
            logger = logging.getLogger(__name__)
            logger.info(f"Logging configured successfully from: {config_path}")
            
        except Exception as e:
            # Fallback to basic configuration
            logging.basicConfig(
                level=default_level,
                format='[%(asctime)s] %(levelname)-8s %(name)-15s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to load logging config from {config_path}: {e}")
            logger.info("Using basic logging configuration as fallback")
    else:
        # Fallback to basic configuration
        logging.basicConfig(
            level=default_level,
            format='[%(asctime)s] %(levelname)-8s %(name)-15s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logger = logging.getLogger(__name__)
        logger.warning(f"Logging config file not found at: {config_path}")
        logger.info("Using basic logging configuration")
    
    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (typically __name__ from calling module)
        
    Returns:
        Logger instance
    """
    # Ensure logging is configured
    setup_logging()
    
    # Create and return logger
    logger = logging.getLogger(name)
    
    return logger


class ToolLogger:
    """
    Specialized logger for tool operations with predefined log formats
    """
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
        self.tool_name = name.split('.')[-1] if '.' in name else name
    
    def tool_start(self, tool_name: str, **kwargs):
        """Log tool execution start"""
        params = ", ".join([f"{k}='{v}'" for k, v in kwargs.items()])
        self.logger.info(f"[TOOL] {tool_name}({params})")
    
    def tool_debug(self, message: str):
        """Log debug information during tool execution"""
        self.logger.debug(f"[DEBUG] {message}")
    
    def tool_info(self, message: str):
        """Log information during tool execution"""
        self.logger.info(f"[INFO] {message}")
    
    def tool_warning(self, message: str):
        """Log warning during tool execution"""
        self.logger.warning(f"[WARNING] {message}")
    
    def tool_error(self, message: str, exc_info: bool = False):
        """Log error during tool execution"""
        self.logger.error(f"[ERROR] {message}", exc_info=exc_info)
    
    def tool_success(self, message: str):
        """Log successful tool completion"""
        self.logger.info(f"[SUCCESS] {message}")


def get_tool_logger(name: str) -> ToolLogger:
    """
    Get a specialized tool logger
    
    Args:
        name: Logger name (typically __name__ from calling module)
        
    Returns:
        ToolLogger instance
    """
    return ToolLogger(name)