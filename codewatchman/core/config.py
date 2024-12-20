from .constants import LogLevel
from dataclasses import dataclass

@dataclass
class CodeWatchmanConfig:
    """Configuration class for CodeWatchman logger."""
    # Code Watchman Remote Server Options
    enable_remote_logging: bool = True
    project_id: str | None = None
    project_secret: str | None = None
    server_url: str = "ws://localhost:8787/log"

    # Console logging options
    console_logging: bool = True
    enable_level_color: bool = True
    enable_message_color: bool = True
    level: LogLevel = LogLevel.DEBUG
    separator_length: int = 80
    format_string: str = "%(asctime)s | %(levelname)s | %(message)s"
    date_format: str = "%Y/%m/%d %H:%M:%S"
    internal_log_level: LogLevel = LogLevel.WARNING

    # Queue options
    max_size: int = 1000  # Maximum number of messages in the queue. Pass 0 for unlimited.
    batch_size: int = 100  # Maximum number of messages in a batch.
    process_interval: float = 1.0 # Time interval in seconds to process the queue.

    shutdown_timeout: float = 5.0 # Timeout for shutting down the queue.

    # WebSocket options
    initial_retry_delay: float = 1.0  # seconds
    max_retry_delay: int = 60
    max_retry_attempts: int = 10
    retry_multiplier: float = 2.0

    # WebSocket keepalive options
    ping_interval: float = 10.0  # seconds
    ping_timeout: float = 10.0   # seconds
