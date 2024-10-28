# codewatchman/core/constants.py

from __future__ import annotations
from enum import IntEnum
from typing import Dict, Final
from colorama import Fore, Style
import logging

# Custom log levels
SUCCESS_LEVEL: Final[int] = logging.INFO + 5
FAILURE_LEVEL: Final[int] = logging.ERROR + 5

# Add custom level names to logging
logging.addLevelName(SUCCESS_LEVEL, 'SUCCESS')
logging.addLevelName(FAILURE_LEVEL, 'FAILURE')

class LogLevel(IntEnum):
    """Enum class for log levels including custom levels."""
    DEBUG = logging.DEBUG        # 10
    INFO = logging.INFO         # 20
    WARNING = logging.WARNING   # 30
    ERROR = logging.ERROR       # 40
    CRITICAL = logging.CRITICAL # 50
    SUCCESS = SUCCESS_LEVEL     # 25
    FAILURE = FAILURE_LEVEL     # 45

# Color mappings for different log levels
LEVEL_COLORS: Final[Dict[int, str]] = {
    LogLevel.DEBUG: Fore.CYAN,
    LogLevel.INFO: Fore.WHITE,
    LogLevel.WARNING: Fore.YELLOW,
    LogLevel.ERROR: Fore.RED,
    LogLevel.CRITICAL: Fore.RED + Style.BRIGHT,
    LogLevel.SUCCESS: Fore.GREEN,
    LogLevel.FAILURE: Fore.RED + Style.BRIGHT
}

# Default format strings
DEFAULT_LOG_FORMAT: Final[str] = "[%(asctime)s] %(levelname)-8s - %(message)s"
DETAILED_LOG_FORMAT: Final[str] = (
    "[%(asctime)s] %(levelname)-8s - %(message)s "
    "%(extra_prefix)s%(extra)s%(extra_suffix)s"
)

# Separator characters and styles
SEPARATOR_CHAR: Final[str] = "-"
SEPARATOR_LENGTH: Final[int] = 50
SEPARATOR_STYLE: Final[str] = Style.DIM

# Default configuration values
DEFAULT_CONFIG: Final[Dict[str, any]] = {
    'server_url': 'wss://api.codewatchman.com/v1/logs',
    'queue_size': 1000,
    'retry_attempts': 3,
    'retry_delay': 1.0,
    'timeout': 5.0,
    'log_format': DEFAULT_LOG_FORMAT,
    'detailed_format': DETAILED_LOG_FORMAT,
    'date_format': '%Y-%m-%d %H:%M:%S',
    'use_colors': True,
    'queue_worker_interval': 0.1,
    'max_batch_size': 100,
}

# Extra payload formatting
EXTRA_PREFIX: Final[str] = " {"
EXTRA_SUFFIX: Final[str] = "}"