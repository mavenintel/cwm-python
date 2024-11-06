from .constants import LogLevel
from dataclasses import dataclass
from urllib.parse import urlparse

@dataclass
class CodeWatchmanConfig:
    """Configuration class for CodeWatchman logger."""
    project_id: str
    project_secret: str
    server_url: str = "ws://localhost:8787/log"

    # Console logging options
    console_logging: bool = True
    enable_level_color: bool = True
    enable_message_color: bool = True
    level: LogLevel = LogLevel.DEBUG
    separator_length: int = 80

    format_string: str = "%(asctime)s | %(levelname)s | %(message)s"
    date_format: str = "%Y/%m/%d %H:%M:%S"

    # Queue options
    max_size: int = 1000
    batch_size: int = 100
    batch_interval: float = 1.0  # seconds
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds

    # WebSocket options
    initial_retry_delay: float = 1.0  # seconds
    max_retry_delay: int = 60
    max_retry_attempts: int = 10
    retry_multiplier: float = 2.0

    # WebSocket keepalive options
    ping_interval: float = 10.0  # seconds
    ping_timeout: float = 10.0   # seconds

    # System metrics options
    enable_gpu: bool = False    # Whether to collect GPU metrics
    gpu_collect_interval: float = 5.0  # How often to collect GPU metrics (seconds)

    def __post_init__(self) -> None:
        """Validate configuration values."""
        self.validate_project_credentials()
        self.validate_server_url()
        self.validate_level()
        self.validate_metrics_config()

    def validate_project_credentials(self) -> None:
        """Validate project credentials."""
        if not self.project_id or not isinstance(self.project_id, str):
            raise ValueError("project_id must be a non-empty string")

        if not self.project_secret or not isinstance(self.project_secret, str):
            raise ValueError("project_secret must be a non-empty string")

    def validate_server_url(self) -> None:
        """Validate server URL format."""
        try:
            parsed = urlparse(self.server_url)
            if parsed.scheme not in ('ws', 'wss'):
                raise ValueError("server_url must use ws:// or wss:// protocol")
            if not parsed.netloc:
                raise ValueError("Invalid server URL format")
        except Exception as e:
            raise ValueError(f"Invalid server URL: {str(e)}")

    def validate_level(self) -> None:
        """Validate logging level."""
        if not isinstance(self.level, int) or self.level not in [
            LogLevel.DEBUG,
            LogLevel.INFO,
            LogLevel.WARNING,
            LogLevel.ERROR,
            LogLevel.CRITICAL,
            LogLevel.SUCCESS,
            LogLevel.FAILURE
        ]:
            raise ValueError("Invalid logging level")

    def validate_metrics_config(self) -> None:
        """Validate metrics configuration."""
        if not isinstance(self.enable_gpu, bool):
            raise ValueError("enable_gpu must be a boolean")

        if not isinstance(self.gpu_collect_interval, (int, float)):
            raise ValueError("gpu_collect_interval must be a number")

        if self.gpu_collect_interval < 0:
            raise ValueError("gpu_collect_interval must be positive")