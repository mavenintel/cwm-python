# codewatchman/core/config.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import logging

from .constants import DEFAULT_CONFIG, LogLevel

@dataclass
class CodeWatchmanConfig:
    """Configuration class for CodeWatchman logger.

    Args:
        project_id: Unique identifier for the project
        project_secret: Authentication secret for the project
        server_url: WebSocket server URL (default: from DEFAULT_CONFIG)
        queue_size: Maximum size of the message queue (default: from DEFAULT_CONFIG)
        retry_attempts: Number of retry attempts for failed operations (default: from DEFAULT_CONFIG)
        retry_delay: Delay between retry attempts in seconds (default: from DEFAULT_CONFIG)
        timeout: Connection timeout in seconds (default: from DEFAULT_CONFIG)
        log_format: Format string for log messages (default: from DEFAULT_CONFIG)
        detailed_format: Format string for detailed log messages (default: from DEFAULT_CONFIG)
        date_format: Format string for timestamps (default: from DEFAULT_CONFIG)
        use_colors: Whether to use colors in console output (default: from DEFAULT_CONFIG)
        level: Logging level (default: INFO)

    Raises:
        ValueError: If any configuration values are invalid
    """
    project_id: str
    project_secret: str
    server_url: str = field(default=DEFAULT_CONFIG['server_url'])
    queue_size: int = field(default=DEFAULT_CONFIG['queue_size'])
    retry_attempts: int = field(default=DEFAULT_CONFIG['retry_attempts'])
    retry_delay: float = field(default=DEFAULT_CONFIG['retry_delay'])
    timeout: float = field(default=DEFAULT_CONFIG['timeout'])
    log_format: str = field(default=DEFAULT_CONFIG['log_format'])
    detailed_format: str = field(default=DEFAULT_CONFIG['detailed_format'])
    date_format: str = field(default=DEFAULT_CONFIG['date_format'])
    use_colors: bool = field(default=DEFAULT_CONFIG['use_colors'])
    level: int = field(default=LogLevel.INFO)
    extra: Optional[Dict[str, Any]] = field(default=None)

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        self.validate_project_credentials()
        self.validate_server_url()
        self.validate_queue_settings()
        self.validate_retry_settings()
        self.validate_timeout()
        self.validate_level()

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

    def validate_queue_settings(self) -> None:
        """Validate queue-related settings."""
        if not isinstance(self.queue_size, int) or self.queue_size <= 0:
            raise ValueError("queue_size must be a positive integer")

    def validate_retry_settings(self) -> None:
        """Validate retry-related settings."""
        if not isinstance(self.retry_attempts, int) or self.retry_attempts < 0:
            raise ValueError("retry_attempts must be a non-negative integer")

        if not isinstance(self.retry_delay, (int, float)) or self.retry_delay < 0:
            raise ValueError("retry_delay must be a non-negative number")

    def validate_timeout(self) -> None:
        """Validate timeout setting."""
        if not isinstance(self.timeout, (int, float)) or self.timeout <= 0:
            raise ValueError("timeout must be a positive number")

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the configuration
        """
        return {
            'project_id': self.project_id,
            'project_secret': self.project_secret,
            'server_url': self.server_url,
            'queue_size': self.queue_size,
            'retry_attempts': self.retry_attempts,
            'retry_delay': self.retry_delay,
            'timeout': self.timeout,
            'log_format': self.log_format,
            'detailed_format': self.detailed_format,
            'date_format': self.date_format,
            'use_colors': self.use_colors,
            'level': self.level,
            'extra': self.extra
        }