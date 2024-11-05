import logging
from colorama import Fore, Style
from enum import IntEnum, Enum

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"

SEPARATOR = "---separator---"

COLORS = {
    logging.DEBUG: Fore.CYAN,
    logging.INFO: Fore.WHITE,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.RED + Style.BRIGHT,
    25: Fore.GREEN,  # SUCCESS
    45: Fore.RED,    # FAILURE
}

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