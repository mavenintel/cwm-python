from __future__ import annotations
import logging
from enum import IntEnum

# Custom log levels
class LogLevel(IntEnum):
    """Enum class for log levels including custom levels."""
    DEBUG = logging.DEBUG       # 10
    INFO = logging.INFO         # 20
    WARNING = logging.WARNING   # 30
    ERROR = logging.ERROR       # 40
    CRITICAL = logging.CRITICAL # 50
    SUCCESS = logging.INFO + 5  # 25
    FAILURE = logging.ERROR + 5 # 45

# Add custom level names to logging
logging.addLevelName(LogLevel.SUCCESS, "SUCCESS")
logging.addLevelName(LogLevel.FAILURE, "FAILURE")

# ANSI Color codes
class Colors:
    DEBUG = "\033[36m"     # Cyan
    INFO = "\033[37m"      # White
    WARNING = "\033[33m"   # Yellow
    ERROR = "\033[31m"     # Red
    CRITICAL = "\033[35m"  # Magenta
    SUCCESS = "\033[32m"   # Green
    FAILURE = "\033[91m"   # Bright Red
    RESET = "\033[0m"      # Reset