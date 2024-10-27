import os
import logging
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, fields, field

class LogLevel(int, Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    SUCCESS = logging.INFO


@dataclass
class CodeWatchmanConfig:
    # Project Name or Sprint Name
    name: str = field(default="default")
    # Logger Level
    level: LogLevel = field(default=LogLevel.INFO)

    # Authorization
    project_id: Optional[str] = field(default=None)
    project_secret: Optional[str] = field(default=None)

    sep_length: int = field(default=50)

    # WebSocket Configuration
    websocket_url: str = field(default="ws://localhost:8787/log")
    websocket_reconnect_attempts: int = field(default=3)
    websocket_reconnect_delay: int = field(default=5)  # seconds

    # API Configuration
    api_url: str = field(default="http://localhost:8787")
    api_timeout: int = field(default=30)  # seconds

    # Local Logging
    local_log_file: Optional[str] = field(default=None)
    local_log_format: str = field(default="%(asctime)s | %(levelname)s: %(message)s")
    local_log_date_format: str = field(default="%d-%b-%Y %H:%M:%S")

    # Console Output
    enable_colors: bool = field(default=True)
    enable_unicode: bool = field(default=True)

    # Performance
    batch_size: int = field(default=100)
    flush_interval: int = field(default=5)  # seconds

    timeout: int = field(default=10)  # seconds
    close_timeout: int = field(default=10)  # seconds


    def __post_init__(self):
        # Load from environment variables if not provided
        if not self.project_id:
            self.project_id = os.environ.get("CODEWATCHMAN_PROJECT_ID")

        if not self.project_secret:
            self.project_secret = os.environ.get("CODEWATCHMAN_PROJECT_SECRET")

        self.has_auth = all([self.project_id, self.project_secret])

        # Convert level to logging level
        self.logging_level = getattr(logging, self.level.name)


    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'CodeWatchmanConfig':
        """Create a configuration instance from a dictionary."""
        return cls(**{
            k: v for k, v in config_dict.items()
            if k in [field.name for field in fields(cls)]
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            field.name: getattr(self, field.name)
            for field in fields(self)
        }


    def validate(self) -> bool:
        """Validate the current configuration."""
        if not self.websocket_url.startswith(('ws://', 'wss://')):
            raise ValueError("Invalid WebSocket URL")

        if not self.api_url.startswith(('http://', 'https://')):
            raise ValueError("Invalid API URL")

        if self.websocket_reconnect_attempts < 0:
            raise ValueError("reconnect_attempts must be non-negative")

        if self.websocket_reconnect_delay < 1:
            raise ValueError("reconnect_delay must be positive")

        if self.api_timeout < 1:
            raise ValueError("api_timeout must be positive")

        if self.timeout < 1:
            raise ValueError("timeout must be positive")

        if self.close_timeout < 1:
            raise ValueError("close_timeout must be positive")

        if self.batch_size < 1:
            raise ValueError("batch_size must be positive")

        if self.flush_interval < 1:
            raise ValueError("flush_interval must be positive")

        return True

default_config = CodeWatchmanConfig()