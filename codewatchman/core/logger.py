from __future__ import annotations
import logging
from typing import Any, Optional, Dict
from dataclasses import dataclass
from ..handlers.console import ConsoleHandler
from .constants import (
    LogLevel,
    SUCCESS_LEVEL,
    FAILURE_LEVEL,
    DEFAULT_CONFIG
)

@dataclass
class CodeWatchmanConfig:
    project_id: str
    project_secret: str
    server_url: str = DEFAULT_CONFIG['server_url']
    queue_size: int = DEFAULT_CONFIG['queue_size']
    retry_attempts: int = DEFAULT_CONFIG['retry_attempts']
    retry_delay: float = DEFAULT_CONFIG['retry_delay']
    timeout: float = DEFAULT_CONFIG['timeout']
    log_format: str = DEFAULT_CONFIG['log_format']
    date_format: str = DEFAULT_CONFIG['date_format']
    use_colors: bool = DEFAULT_CONFIG['use_colors']

class CodeWatchman(logging.Logger):
    """Main logger class for CodeWatchman."""

    def __init__(
        self,
        config: CodeWatchmanConfig,
        name: str = "codewatchman",
        level: int = logging.INFO
    ) -> None:
        """Initialize CodeWatchman logger.

        Args:
            config: Configuration object
            name: Logger name
            level: Initial logging level
        """
        super().__init__(name, level)
        self.config = config

        # Set up console handler
        console_handler = ConsoleHandler(
            use_colors=config.use_colors,
            fmt=config.log_format,
            date_fmt=config.date_format
        )
        self.addHandler(console_handler)

    def success(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a success message.

        Args:
            msg: Message to log
            *args: Variable positional arguments
            **kwargs: Variable keyword arguments
        """
        self.log(SUCCESS_LEVEL, msg, *args, **kwargs)

    def failure(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a failure message.

        Args:
            msg: Message to log
            *args: Variable positional arguments
            **kwargs: Variable keyword arguments
        """
        self.log(FAILURE_LEVEL, msg, *args, **kwargs)

    def sep(self):
        """Add a separator line to the logs"""
        separator = "-" * 50
        self.info(separator)

    def __enter__(self) -> CodeWatchman:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit with cleanup."""
        self.handlers.clear()