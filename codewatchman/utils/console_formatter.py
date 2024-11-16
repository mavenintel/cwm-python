import logging
from colorama import Style

from ..core.constants import COLORS, SEPARATOR
from ..core.config import CodeWatchmanConfig

class ConsoleFormatter(logging.Formatter):
    """Console formatter"""
    def __init__(self, config: CodeWatchmanConfig, **kwargs):
        super().__init__(**kwargs, fmt=config.format_string, datefmt=config.date_format)
        self.config = config

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors."""

        color = COLORS.get(record.levelno, Style.RESET_ALL)

        if record.msg == SEPARATOR:
            msg = "-" * self.config.separator_length
            return f"{color}{msg}{Style.RESET_ALL}"

        if isinstance(record.msg, tuple) and record.msg[0] == SEPARATOR:
            # Handle separator with name
            name = record.msg[1]
            padding = (self.config.separator_length - len(name) - 2) // 2  # -2 for spaces around name
            left_pad = "-" * padding
            right_pad = "-" * (self.config.separator_length - padding - len(name) - 2)
            msg = f"{left_pad} {name} {right_pad}"
            return f"{color}{msg}{Style.RESET_ALL}"

        record.levelname = record.levelname.ljust(8)

        if self.config.enable_level_color:
            record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"

        if self.config.enable_message_color:
            record.msg = f"{color}{record.msg}{Style.RESET_ALL}"

        return super().format(record)


