import logging
from colorama import Fore, Style, Back
from enum import IntEnum, Enum

SEPARATOR = "---separator---"

COLORS = {
    logging.DEBUG: Fore.CYAN,
    15: Fore.WHITE, # SEPARATOR
    logging.INFO: Fore.MAGENTA,
    logging.WARNING: Fore.LIGHTYELLOW_EX,
    logging.ERROR: Fore.YELLOW,
    logging.CRITICAL: Back.RED + Fore.WHITE + Style.BRIGHT,
    25: Fore.GREEN + Style.BRIGHT,  # SUCCESS
    45: Fore.RED + Style.BRIGHT,    # FAILURE
}

# Custom log levels
class LogLevel(IntEnum):
    """Enum class for log levels including custom levels."""
    DEBUG = logging.DEBUG            # 10
    SEPARATOR = logging.DEBUG + 5    # 15
    INFO = logging.INFO              # 20
    WARNING = logging.WARNING        # 30
    ERROR = logging.ERROR            # 40
    CRITICAL = logging.CRITICAL      # 50
    SUCCESS = logging.INFO + 5       # 25
    FAILURE = logging.ERROR + 5  # 45

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"