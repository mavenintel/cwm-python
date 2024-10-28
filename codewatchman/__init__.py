"""
CodeWatchman
-----------
A non-blocking logging library that sends logs to both console and server.
"""

from .logger import CodeWatchman
from .config import CodeWatchmanConfig

# Package metadata
__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2024"

# Custom log levels registration
import logging

# Register custom log levels if they don't exist
if not hasattr(logging, 'SUCCESS'):
    SUCCESS = 25  # Between INFO and WARNING
    logging.addLevelName(SUCCESS, 'SUCCESS')

if not hasattr(logging, 'FAILURE'):
    FAILURE = 45  # Between ERROR and CRITICAL
    logging.addLevelName(FAILURE, 'FAILURE')

# Export main classes
__all__ = [
    'CodeWatchman',
    'CodeWatchmanConfig',
]

# Optional: Add a convenience function to quickly set up a logger
def setup_logger(
    project_id: str,
    project_secret: str,
    **kwargs
) -> CodeWatchman:
    """
    Convenience function to quickly set up a CodeWatchman logger with default settings.

    Args:
        project_id (str): Your project ID
        project_secret (str): Your project secret
        **kwargs: Additional configuration options for CodeWatchmanConfig

    Returns:
        CodeWatchman: Configured logger instance

    Example:
        >>> logger = setup_logger("my-project-id", "my-project-secret")
        >>> logger.info("Hello, World!")
    """
    config = CodeWatchmanConfig(
        project_id=project_id,
        project_secret=project_secret,
        **kwargs
    )
    return CodeWatchman(config=config)