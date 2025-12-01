"""
Logging Utility Module

Provides structured logging with different levels and outputs.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class LogConfig:
    """Configuration for logging"""
    level: str = "INFO"
    console_enabled: bool = True
    file_enabled: bool = False
    file_path: Optional[str] = None


class Logger:
    """Structured logging utility"""
    
    def __init__(self, name: str, config: LogConfig):
        """Initialize a logger with configuration."""
        self.name = name
        self.config = config
        self.logger = logging.getLogger(name)
        
        # Set level
        self.logger.setLevel(getattr(logging, config.level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if config.console_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(getattr(logging, config.level.upper()))
            self.logger.addHandler(console_handler)
        
        # File handler
        if config.file_enabled and config.file_path:
            # Ensure directory exists
            Path(config.file_path).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(config.file_path)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, config.level.upper()))
            self.logger.addHandler(file_handler)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message"""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message"""
        self.logger.debug(message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message"""
        self.logger.critical(message, **kwargs)


def setup_logging(level: str = "INFO", 
                  console_enabled: bool = True,
                  file_enabled: bool = False,
                  file_path: Optional[str] = None) -> Logger:
    """
    Setup logging configuration
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_enabled: Enable console logging
        file_enabled: Enable file logging
        file_path: Path to log file
    
    Returns:
        Configured Logger instance
    """
    config = LogConfig(
        level=level,
        console_enabled=console_enabled,
        file_enabled=file_enabled,
        file_path=file_path
    )
    return Logger("homeamp", config)
