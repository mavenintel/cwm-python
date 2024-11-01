from __future__ import annotations

import logging
from typing import Optional

from .constants import LogLevel, SEPARATOR
from ..handlers import ConsoleHandler
from .config import CodeWatchmanConfig

class CodeWatchman(logging.Logger):
    def __init__(self, config: CodeWatchmanConfig, name: str = "CodeWatchman"):
        super().__init__(name, config.level)

        # Register custom log levels
        logging.addLevelName(LogLevel.SUCCESS, "SUCCESS")
        logging.addLevelName(LogLevel.FAILURE, "FAILURE")

        self.config = config

        # Enable propagation to root logger
        self.propagate = True

        # Create console handler with colored formatting
        if config.console_logging:
            self.addHandler(ConsoleHandler(config))

    def success(self, msg: str, *args, **kwargs) -> None:
        """Log a success message.

        Args:
            msg: Message to log
            *args: Variable positional arguments
            **kwargs: Variable keyword arguments
        """
        self.log(LogLevel.SUCCESS, msg, *args, **kwargs)

    def failure(self, msg: str, *args, **kwargs) -> None:
        """Log a failure message.

        Args:
            msg: Message to log
            *args: Variable positional arguments
            **kwargs: Variable keyword arguments
        """
        self.log(LogLevel.FAILURE, msg, *args, **kwargs)

    def sep(self, name: Optional[str] = None) -> None:
        """Add a separator line to the logs"""
        self.info((SEPARATOR, name) if name else SEPARATOR)

    def __enter__(self) -> CodeWatchman:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Context manager exit with cleanup."""
        self.handlers.clear()

    def close(self) -> None:
        self.handlers.clear()
