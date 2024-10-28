# codewatchman/handlers/console.py

from __future__ import annotations
import logging
import json
from typing import Any, Dict, Optional
from colorama import Style

from ..core.constants import (
    LEVEL_COLORS,
    EXTRA_PREFIX,
    EXTRA_SUFFIX
)

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors and handles extra payload.

    Args:
        fmt: Format string for the message
        date_fmt: Format string for the timestamp
        use_colors: Whether to use colors in output
    """
    def __init__(
        self,
        fmt: Optional[str] = None,
        date_fmt: Optional[str] = None,
        use_colors: bool = True
    ) -> None:
        super().__init__(fmt=fmt, datefmt=date_fmt)
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors and extra payload.

        Args:
            record: LogRecord instance to format

        Returns:
            str: Formatted log message
        """
        # Add color to the level name if colors are enabled
        if self.use_colors and record.levelno in LEVEL_COLORS:
            record.levelname = (
                f"{LEVEL_COLORS[record.levelno]}"
                f"{record.levelname}"
                f"{Style.RESET_ALL}"
            )

        # Handle extra payload
        record.extra_prefix = ""
        record.extra_suffix = ""
        record.extra = ""

        if hasattr(record, 'extra') and record.extra:
            try:
                extra_str = json.dumps(record.extra, sort_keys=True)
                record.extra_prefix = EXTRA_PREFIX
                record.extra_suffix = EXTRA_SUFFIX
                record.extra = extra_str
            except Exception:
                record.extra = str(record.extra)

        return super().format(record)

class ConsoleHandler(logging.StreamHandler):
    """Custom console handler with colored output and payload formatting.

    Args:
        formatter: Custom formatter instance (default: ColoredFormatter)
        use_colors: Whether to use colors in output
        fmt: Format string for the message
        date_fmt: Format string for the timestamp
    """
    def __init__(
        self,
        formatter: Optional[logging.Formatter] = None,
        use_colors: bool = True,
        fmt: Optional[str] = None,
        date_fmt: Optional[str] = None
    ) -> None:
        super().__init__()

        if formatter is None:
            formatter = ColoredFormatter(
                fmt=fmt,
                date_fmt=date_fmt,
                use_colors=use_colors
            )

        self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record with exception handling.

        Args:
            record: LogRecord instance to emit
        """
        try:
            super().emit(record)
            self.flush()
        except Exception:
            self.handleError(record)