from __future__ import annotations
import logging
import sys
from typing import Any, Optional, Dict
from colorama import init

from .config import CodeWatchmanConfig
from .constants import LogLevel, Colors

# Initialize colorama for cross-platform color support
init()

class CodeWatchman(logging.Logger):
    def __init__(
        self,
        config: CodeWatchmanConfig,
        level: int = logging.INFO,
        name: str = "codewatchman"
    ) -> None:
        """Initialize the CodeWatchman logger."""
        super().__init__(name, level)
        self.config = config

        # Create console handler with colored formatting
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColoredFormatter())
        self.addHandler(console_handler)

    def success(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a success message."""
        if self.isEnabledFor(LogLevel.SUCCESS):
            self._log(LogLevel.SUCCESS, msg, args, **kwargs)

    def failure(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a failure message."""
        if self.isEnabledFor(LogLevel.FAILURE):
            self._log(LogLevel.FAILURE, msg, args, **kwargs)

    def sep(self, char: str = "-", length: int = 50) -> None:
        """Print a separator line."""
        self.info(char * length)

    def close(self) -> None:
        """Close the logger and clean up resources."""
        for handler in self.handlers[:]:
            handler.close()
            self.removeHandler(handler)


class ColoredFormatter(logging.Formatter):
    """Custom formatter adding colors to log output."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.level_colors = {
            logging.DEBUG: Colors.DEBUG,
            logging.INFO: Colors.INFO,
            logging.WARNING: Colors.WARNING,
            logging.ERROR: Colors.ERROR,
            logging.CRITICAL: Colors.CRITICAL,
            LogLevel.SUCCESS: Colors.SUCCESS,
            LogLevel.FAILURE: Colors.FAILURE,
        }

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors."""
        color = self.level_colors.get(record.levelno, Colors.RESET)
        record.levelname = f"{color}{record.levelname}{Colors.RESET}"
        record.msg = f"{color}{record.msg}{Colors.RESET}"
        return super().format(record)