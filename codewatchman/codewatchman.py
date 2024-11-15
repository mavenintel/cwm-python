from __future__ import annotations

import logging
from typing import Optional

from .handlers import ConsoleHandler
from .core.config import CodeWatchmanConfig
from .core.constants import LogLevel, SEPARATOR

class CodeWatchman(logging.Logger):
    """
        CodeWatchman logger class.
        Extends the standard logging.Logger class with custom log levels and remote logging support.
    """
    def __init__(self, config: Optional[CodeWatchmanConfig] = None, name: str = "CodeWatchman"):
        super().__init__(name, config.level)

        if config is None:
            config = CodeWatchmanConfig()

        self.config = config
        self.logger = logging.getLogger(name)
        logging.basicConfig(level=config.level)

        # Create console handler with colored formatting
        if config.console_logging:
            self.addHandler(ConsoleHandler(config))

        # Disable noisy log messages
        # logging.getLogger("asyncio").setLevel(logging.WARNING)
        # logging.getLogger("websockets").setLevel(logging.WARNING)

        # Register custom log levels
        logging.addLevelName(LogLevel.SUCCESS, "SUCCESS")
        logging.addLevelName(LogLevel.FAILURE, "FAILURE")


    def success(self, msg: str, *args, **kwargs) -> None:
        """Log a success message."""
        self.log(LogLevel.SUCCESS, msg, *args, **kwargs)

    def failure(self, msg: str, *args, **kwargs) -> None:
        """Log a failure message."""
        self.log(LogLevel.FAILURE, msg, *args, **kwargs)

    def sep(self, name: Optional[str] = None) -> None:
        """Add a separator line to the logs"""
        self.log(LogLevel.SEPARATOR, (SEPARATOR, name) if name else SEPARATOR)

    def _log(self, level: LogLevel, msg: str | tuple[str, str], *args, **kwargs) -> None:
        """Log a message with the given level."""
        super()._log(level, msg, *args, **kwargs)


    def process_messages(self) -> None:
        """Process messages from the queue."""
        self.queue.process_messages()

    def close(self) -> None:
        """Close the logger and release resources."""
        self.logger.info(f"Closing logger.")

    def __enter__(self) -> CodeWatchman:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Context manager exit with cleanup."""
        self.close()